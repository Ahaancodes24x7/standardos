import { getSession, updateSession, clearSession } from "@tanstack/react-start/server";
import type { SessionConfig } from "@tanstack/react-start/server";

type AuthSessionData = { userId: string };

function config(): SessionConfig {
  const password = process.env["SESSION_SECRET"];
  if (!password || password.length < 32) {
    throw new Error("SESSION_SECRET must be set to a random string of at least 32 characters.");
  }
  return {
    password,
    name: "standardos_session",
    maxAge: 60 * 60 * 24 * 30, // 30 days
    cookie: { sameSite: "lax" },
  };
}

export async function getCurrentUserId(): Promise<string | undefined> {
  const session = await getSession<AuthSessionData>(config());
  return session.data.userId;
}

export async function setAuthSession(userId: string): Promise<void> {
  await updateSession<AuthSessionData>(config(), { userId });
}

export async function destroyAuthSession(): Promise<void> {
  await clearSession(config());
}
