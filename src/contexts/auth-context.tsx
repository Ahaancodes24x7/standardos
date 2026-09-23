import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { getCurrentUser, signOut as signOutRequest, type CurrentUser } from "@/services/auth";

type Profile = { full_name: string; organization: string };
type AuthState = {
  user: CurrentUser | null;
  profile: Profile | null;
  loading: boolean;
  isDemo: boolean;
  signOut: () => Promise<void>;
  activateDemo: () => void;
  refreshProfile: () => Promise<void>;
};
const AuthContext = createContext<AuthState | undefined>(undefined);
const demoProfile = { full_name: "Ahaan Luther", organization: "Infrastructure Procurement Cell" };
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [isDemo, setIsDemo] = useState(false);
  const refreshProfile = async () => {
    const current = await getCurrentUser().catch(() => null);
    setUser(current);
  };
  useEffect(() => {
    const demo = window.localStorage.getItem("standardos-demo") === "true";
    setIsDemo(demo);
    void refreshProfile().finally(() => setLoading(false));
  }, []);
  const value = useMemo(
    () => ({
      user,
      profile: isDemo ? demoProfile : (user?.profile ?? null),
      loading,
      isDemo,
      activateDemo: () => {
        window.localStorage.setItem("standardos-demo", "true");
        setIsDemo(true);
      },
      refreshProfile,
      signOut: async () => {
        window.localStorage.removeItem("standardos-demo");
        setIsDemo(false);
        await signOutRequest().catch(() => null);
        setUser(null);
      },
    }),
    [user, loading, isDemo],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}
export function hasDemoSession() {
  return typeof window !== "undefined" && window.localStorage.getItem("standardos-demo") === "true";
}
