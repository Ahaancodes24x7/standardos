import { Link, useNavigate } from "@tanstack/react-router";
import { ArrowRight, Eye, EyeOff } from "lucide-react";
import { useState, type FormEvent } from "react";
import { toast } from "sonner";
import { Brand } from "@/components/brand";
import { AuthVisual } from "@/components/auth-visual";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/contexts/auth-context";
import { signIn, signUp } from "@/services/auth";
export function AuthForm({ mode }: { mode: "login" | "signup" }) {
  const signup = mode === "signup";
  const navigate = useNavigate();
  const { activateDemo, refreshProfile } = useAuth();
  const [loading, setLoading] = useState(false);
  const [show, setShow] = useState(false);
  const [error, setError] = useState("");
  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    const fd = new FormData(event.currentTarget);
    const email = String(fd.get("email") ?? "").trim();
    const password = String(fd.get("password") ?? "");
    try {
      if (signup) {
        const fullName = String(fd.get("fullName") ?? "").trim();
        const organization = String(fd.get("organization") ?? "").trim();
        const confirm = String(fd.get("confirm") ?? "");
        if (password !== confirm) throw new Error("Passwords do not match.");
        await signUp({ email, password, fullName, organization });
        await refreshProfile();
        await navigate({ to: "/dashboard" });
      } else {
        await signIn({ email, password });
        await refreshProfile();
        await navigate({ to: "/dashboard" });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };
  const demo = () => {
    activateDemo();
    void navigate({ to: "/dashboard" });
  };
  return (
    <div className="grid min-h-screen lg:grid-cols-[.9fr_1.1fr]">
      <div className="flex min-h-screen flex-col px-5 py-7 sm:px-10 lg:px-16">
        <Brand />
        <main className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center py-12">
          <p className="eyebrow">{signup ? "Create your workspace" : "Secure workspace access"}</p>
          <h1 className="mt-3 font-display text-4xl text-primary">
            {signup ? "Start with certainty." : "Welcome back."}
          </h1>
          <p className="mt-3 text-sm leading-6 text-muted-foreground">
            {signup
              ? "Set up a procurement intelligence workspace for your organization."
              : "Continue to your standards and compliance workspace."}
          </p>
          <div className="mt-7 grid gap-3">
            <Button variant="secondary" size="lg" onClick={demo}>
              Continue with Demo Account
            </Button>
          </div>
          <div className="my-6 flex items-center gap-3 text-xs text-muted-foreground">
            <span className="h-px flex-1 bg-border" />
            or use work email
            <span className="h-px flex-1 bg-border" />
          </div>
          <form onSubmit={submit} className="grid gap-4">
            {signup && (
              <>
                <div className="grid gap-1.5">
                  <Label htmlFor="fullName">Full name</Label>
                  <Input
                    id="fullName"
                    name="fullName"
                    required
                    minLength={2}
                    maxLength={100}
                    placeholder="Ahaan Luther"
                  />
                </div>
                <div className="grid gap-1.5">
                  <Label htmlFor="organization">Organization</Label>
                  <Input
                    id="organization"
                    name="organization"
                    required
                    minLength={2}
                    maxLength={160}
                    placeholder="Infrastructure Procurement Cell"
                  />
                </div>
              </>
            )}
            <div className="grid gap-1.5">
              <Label htmlFor="email">Work email</Label>
              <Input
                id="email"
                name="email"
                required
                type="email"
                maxLength={255}
                placeholder="name@organization.in"
              />
            </div>
            <div className="grid gap-1.5">
              <div className="flex justify-between">
                <Label htmlFor="password">Password</Label>
                {!signup && (
                  <Link
                    to="/forgot-password"
                    className="text-xs font-semibold text-accent-foreground hover:underline"
                  >
                    Forgot password?
                  </Link>
                )}
              </div>
              <div className="relative">
                <Input
                  id="password"
                  name="password"
                  required
                  minLength={8}
                  maxLength={72}
                  type={show ? "text" : "password"}
                  className="pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShow(!show)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground"
                  aria-label={show ? "Hide password" : "Show password"}
                >
                  {show ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                </button>
              </div>
            </div>
            {signup ? (
              <div className="grid gap-1.5">
                <Label htmlFor="confirm">Confirm password</Label>
                <Input
                  id="confirm"
                  name="confirm"
                  required
                  minLength={8}
                  maxLength={72}
                  type={show ? "text" : "password"}
                />
              </div>
            ) : (
              <label className="flex items-center gap-2 text-sm text-muted-foreground">
                <Checkbox name="remember" />
                Remember me
              </label>
            )}
            {error && (
              <div
                role="alert"
                className="border-l-2 border-destructive bg-destructive/5 px-3 py-2 text-sm text-destructive"
              >
                {error}
              </div>
            )}
            <Button size="lg" type="submit" disabled={loading}>
              {loading ? "Please wait…" : signup ? "Create account" : "Sign in"}
              <ArrowRight />
            </Button>
          </form>
          <p className="mt-6 text-center text-sm text-muted-foreground">
            {signup ? "Already have an account? " : "New to STANDARDOS? "}
            <Link
              to={signup ? "/login" : "/signup"}
              className="font-bold text-accent-foreground hover:underline"
            >
              {signup ? "Sign in" : "Create account"}
            </Link>
          </p>
        </main>
      </div>
      <aside className="relative hidden overflow-hidden border-l border-border bg-primary lg:block">
        <AuthVisual />
        <div className="relative flex h-full flex-col justify-end p-16 text-primary-foreground">
          <p className="eyebrow text-accent">Specifications to certainty</p>
          <blockquote className="mt-4 max-w-xl font-display text-3xl leading-snug">
            Every requirement should lead to evidence. Every decision should withstand review.
          </blockquote>
        </div>
      </aside>
    </div>
  );
}
