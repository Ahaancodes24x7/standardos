import { createServerFn } from "@tanstack/react-start";
import { eq } from "drizzle-orm";
import { randomBytes } from "node:crypto";
import { z } from "zod";
import { db, schema } from "@/lib/db.server";
import { hashPassword, hashToken, verifyPassword } from "@/lib/password.server";
import { destroyAuthSession, getCurrentUserId, setAuthSession } from "@/lib/session.server";

export type Profile = { full_name: string; organization: string };
export type CurrentUser = { id: string; email: string; profile: Profile };

const emailSchema = z
  .string()
  .trim()
  .toLowerCase()
  .email()
  .max(255);
const passwordSchema = z.string().min(8).max(72);

async function loadCurrentUser(userId: string): Promise<CurrentUser | null> {
  const user = await db.query.users.findFirst({ where: eq(schema.users.id, userId) });
  if (!user) return null;
  const profile = await db.query.profiles.findFirst({ where: eq(schema.profiles.userId, userId) });
  return {
    id: user.id,
    email: user.email,
    profile: profile
      ? { full_name: profile.fullName, organization: profile.organization }
      : { full_name: user.email.split("@")[0] ?? "User", organization: "My workspace" },
  };
}

export const getCurrentUserFn = createServerFn({ method: "GET" }).handler(
  async (): Promise<CurrentUser | null> => {
    const userId = await getCurrentUserId();
    if (!userId) return null;
    return loadCurrentUser(userId);
  },
);

export const signUpFn = createServerFn({ method: "POST" })
  .validator((data: unknown) =>
    z
      .object({
        email: emailSchema,
        password: passwordSchema,
        fullName: z.string().trim().min(1).max(100),
        organization: z.string().trim().min(1).max(160),
      })
      .parse(data),
  )
  .handler(async ({ data }): Promise<CurrentUser> => {
    const existing = await db.query.users.findFirst({ where: eq(schema.users.email, data.email) });
    if (existing) throw new Error("An account with this email already exists.");

    const passwordHash = await hashPassword(data.password);
    let user: typeof schema.users.$inferSelect;
    try {
      user = await db.transaction(async (tx) => {
        const [createdUser] = await tx
          .insert(schema.users)
          .values({ email: data.email, passwordHash })
          .returning();
        if (!createdUser) throw new Error("Failed to create account.");
        await tx.insert(schema.profiles).values({
          userId: createdUser.id,
          fullName: data.fullName,
          organization: data.organization,
        });
        return createdUser;
      });
    } catch (error) {
      // Postgres unique_violation — guards the race between the existence
      // check above and this insert.
      if (typeof error === "object" && error !== null && "code" in error && error.code === "23505") {
        throw new Error("An account with this email already exists.");
      }
      throw error;
    }

    await setAuthSession(user.id);
    return { id: user.id, email: user.email, profile: { full_name: data.fullName, organization: data.organization } };
  });

export const signInFn = createServerFn({ method: "POST" })
  .validator((data: unknown) => z.object({ email: emailSchema, password: z.string().min(1).max(72) }).parse(data))
  .handler(async ({ data }): Promise<CurrentUser> => {
    const invalidCredentials = () => new Error("Invalid email or password.");
    const user = await db.query.users.findFirst({ where: eq(schema.users.email, data.email) });
    if (!user) throw invalidCredentials();

    const valid = await verifyPassword(data.password, user.passwordHash);
    if (!valid) throw invalidCredentials();

    await setAuthSession(user.id);
    const current = await loadCurrentUser(user.id);
    if (!current) throw invalidCredentials();
    return current;
  });

export const signOutFn = createServerFn({ method: "POST" }).handler(async () => {
  await destroyAuthSession();
  return null;
});

export const updateProfileFn = createServerFn({ method: "POST" })
  .validator((data: unknown) =>
    z.object({ fullName: z.string().trim().min(1).max(100), organization: z.string().trim().min(1).max(160) }).parse(data),
  )
  .handler(async ({ data }): Promise<Profile> => {
    const userId = await getCurrentUserId();
    if (!userId) throw new Error("Your session expired. Please sign in again.");
    await db
      .update(schema.profiles)
      .set({ fullName: data.fullName, organization: data.organization, updatedAt: new Date() })
      .where(eq(schema.profiles.userId, userId));
    return { full_name: data.fullName, organization: data.organization };
  });

export const updatePasswordFn = createServerFn({ method: "POST" })
  .validator((data: unknown) => z.object({ password: passwordSchema }).parse(data))
  .handler(async ({ data }) => {
    const userId = await getCurrentUserId();
    if (!userId) throw new Error("Your session expired. Please sign in again.");
    const passwordHash = await hashPassword(data.password);
    await db.update(schema.users).set({ passwordHash }).where(eq(schema.users.id, userId));
    return { ok: true as const };
  });

const RESET_TOKEN_TTL_MS = 60 * 60 * 1000; // 1 hour

export const requestPasswordResetFn = createServerFn({ method: "POST" })
  .validator((data: unknown) => z.object({ email: emailSchema }).parse(data))
  .handler(async ({ data }): Promise<{ ok: true; resetUrl?: string }> => {
    const user = await db.query.users.findFirst({ where: eq(schema.users.email, data.email) });
    // Always return { ok: true } regardless of whether the account exists,
    // to avoid trivially leaking which emails are registered.
    if (!user) return { ok: true };

    const token = randomBytes(32).toString("hex");
    await db.insert(schema.passwordResetTokens).values({
      userId: user.id,
      tokenHash: hashToken(token),
      expiresAt: new Date(Date.now() + RESET_TOKEN_TTL_MS),
    });

    // No email provider is configured yet, so the link is handed back
    // directly instead of being sent — see src/routes/forgot-password.tsx.
    return { ok: true, resetUrl: `/reset-password?token=${token}` };
  });

export const resetPasswordFn = createServerFn({ method: "POST" })
  .validator((data: unknown) => z.object({ token: z.string().min(1), password: passwordSchema }).parse(data))
  .handler(async ({ data }) => {
    const invalidLink = () => new Error("This reset link is invalid or has expired.");
    const tokenHash = hashToken(data.token);
    const record = await db.query.passwordResetTokens.findFirst({
      where: eq(schema.passwordResetTokens.tokenHash, tokenHash),
    });
    if (!record || record.usedAt || record.expiresAt.getTime() < Date.now()) throw invalidLink();

    const passwordHash = await hashPassword(data.password);
    await db.transaction(async (tx) => {
      await tx.update(schema.users).set({ passwordHash }).where(eq(schema.users.id, record.userId));
      await tx
        .update(schema.passwordResetTokens)
        .set({ usedAt: new Date() })
        .where(eq(schema.passwordResetTokens.id, record.id));
    });

    return { ok: true as const };
  });
