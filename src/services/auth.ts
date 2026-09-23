import { api } from "@/lib/api";

// Account API (FastAPI /api/auth). The session is an HTTP-only cookie set by
// the backend, so the browser never handles tokens directly.

export type Profile = { full_name: string; organization: string };
export type CurrentUser = { id: string; email: string; profile: Profile };

export const getCurrentUser = () => api.get<CurrentUser | null>("/api/auth/me");

export const signUp = (data: {
  email: string;
  password: string;
  fullName: string;
  organization: string;
}) => api.post<CurrentUser>("/api/auth/signup", data);

export const signIn = (data: { email: string; password: string }) =>
  api.post<CurrentUser>("/api/auth/signin", data);

export const signOut = () => api.post<null>("/api/auth/signout");

export const updateProfile = (data: { fullName: string; organization: string }) =>
  api.patch<Profile>("/api/auth/profile", data);

export const updatePassword = (password: string) =>
  api.post<{ ok: true }>("/api/auth/password", { password });

export const requestPasswordReset = (email: string) =>
  api.post<{ ok: true; resetUrl?: string }>("/api/auth/password-reset/request", { email });

export const resetPassword = (token: string, password: string) =>
  api.post<{ ok: true }>("/api/auth/password-reset/confirm", { token, password });
