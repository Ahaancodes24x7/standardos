import { createHash, randomBytes, scrypt as scryptCallback, timingSafeEqual } from "node:crypto";
import { promisify } from "node:util";

const scrypt = promisify(scryptCallback);
const KEY_LENGTH = 64;

export async function hashPassword(password: string): Promise<string> {
  const salt = randomBytes(16).toString("hex");
  const derivedKey = (await scrypt(password, salt, KEY_LENGTH)) as Buffer;
  return `${salt}:${derivedKey.toString("hex")}`;
}

export async function verifyPassword(password: string, stored: string): Promise<boolean> {
  const [salt, hash] = stored.split(":");
  if (!salt || !hash) return false;
  const derivedKey = (await scrypt(password, salt, KEY_LENGTH)) as Buffer;
  const hashBuffer = Buffer.from(hash, "hex");
  if (hashBuffer.length !== derivedKey.length) return false;
  return timingSafeEqual(hashBuffer, derivedKey);
}

export function hashToken(token: string): string {
  // Reset tokens are high-entropy random values already; a fast SHA-256
  // digest (rather than scrypt) is fine for at-rest storage and lets us
  // look tokens up by exact hash match.
  return createHash("sha256").update(token, "utf8").digest("hex");
}
