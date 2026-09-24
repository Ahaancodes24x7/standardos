import { createFileRoute } from "@tanstack/react-router";
import { Bell, Check, KeyRound, Lock, Save, Shield, User } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { toast } from "sonner";
import { useAuth } from "@/contexts/auth-context";
import { updatePassword as updatePasswordRequest, updateProfile } from "@/services/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { PageHeader } from "@/components/shared/page-header";

export const Route = createFileRoute("/_authenticated/settings")({
  head: () => ({
    meta: [
      { title: "Workspace Settings — STANDARDOS" },
      {
        name: "description",
        content: "Manage your STANDARDOS profile, notifications, and password.",
      },
      { property: "og:title", content: "Workspace Settings — STANDARDOS" },
      { property: "og:description", content: "Manage procurement workspace preferences." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: SettingsPage,
});

function SettingsPage() {
  const { profile, isDemo, refreshProfile } = useAuth();
  const [name, setName] = useState("");
  const [organization, setOrganization] = useState("");
  const [saving, setSaving] = useState(false);
  const [password, setPassword] = useState("");

  useEffect(() => {
    setName(profile?.full_name ?? "");
    setOrganization(profile?.organization ?? "");
  }, [profile]);

  const saveProfile = async (event: FormEvent) => {
    event.preventDefault();
    if (isDemo) {
      toast.success("Demo profile preferences saved for this session.");
      return;
    }
    setSaving(true);
    try {
      await updateProfile({ fullName: name.trim(), organization: organization.trim() });
      await refreshProfile();
      toast.success("Profile updated.");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Something went wrong.");
    }
    setSaving(false);
  };

  const updatePassword = async () => {
    if (password.length < 8) {
      toast.error("Password must be at least 8 characters.");
      return;
    }
    try {
      await updatePasswordRequest(password);
      setPassword("");
      toast.success("Password updated.");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Something went wrong.");
    }
  };

  return (
    <div className="reveal max-w-4xl space-y-8">
      {/* Header */}
      <PageHeader
        eyebrow="Workspace / Settings"
        title="Settings & Preferences"
        description="Manage your professional identity, organization credentials, and notification thresholds."
      />

      {/* Profile Section */}
      <section className="intel-card p-6 space-y-6">
        <div className="flex items-center gap-2.5 border-b border-border/70 pb-3">
          <User className="size-4 text-accent-foreground" />
          <h2 className="text-base font-bold text-primary">Profile Identity</h2>
        </div>

        <form onSubmit={saveProfile} className="grid gap-5 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label
              htmlFor="settings-name"
              className="text-xs font-bold uppercase text-muted-foreground"
            >
              Full Name
            </Label>
            <Input
              id="settings-name"
              value={name}
              onChange={(event) => setName(event.target.value)}
              className="text-xs bg-background"
              required
            />
          </div>

          <div className="space-y-1.5">
            <Label
              htmlFor="settings-org"
              className="text-xs font-bold uppercase text-muted-foreground"
            >
              Procurement Organization
            </Label>
            <Input
              id="settings-org"
              value={organization}
              onChange={(event) => setOrganization(event.target.value)}
              className="text-xs bg-background"
              required
            />
          </div>

          <div className="sm:col-span-2 pt-2">
            <Button type="submit" disabled={saving} size="sm" className="gap-2">
              <Save className="size-3.5" />
              <span>{saving ? "Saving…" : "Save Profile Details"}</span>
            </Button>
          </div>
        </form>
      </section>

      {/* Notifications Section */}
      <section className="intel-card p-6 space-y-5">
        <div className="flex items-center gap-2.5 border-b border-border/70 pb-3">
          <Bell className="size-4 text-accent-foreground" />
          <h2 className="text-base font-bold text-primary">Notification Channels</h2>
        </div>

        <div className="divide-y divide-border/60">
          <Preference
            title="Standards Amendments"
            detail="Alert me immediately when an Indian Standard mapped to an active specification is revised or amended."
            defaultChecked
          />
          <Preference
            title="Compliance Review Reminders"
            detail="Notify me about unresolved high-severity conflicts and normative gaps requiring sign-off."
            defaultChecked
          />
          <Preference
            title="Analysis Pipeline Completion"
            detail="Send desktop notification when an asynchronous document analysis run concludes."
          />
        </div>
      </section>

      {/* Password Security Section */}
      <section className="intel-card p-6 space-y-5">
        <div className="flex items-center gap-2.5 border-b border-border/70 pb-3">
          <KeyRound className="size-4 text-accent-foreground" />
          <h2 className="text-base font-bold text-primary">Authentication Security</h2>
        </div>

        {isDemo ? (
          <div className="rounded-lg border border-border/80 bg-background/50 p-4 text-xs text-muted-foreground">
            Password changes are disabled in demonstration sessions.
          </div>
        ) : (
          <div className="space-y-3 max-w-lg">
            <Label htmlFor="new-pw" className="text-xs font-bold uppercase text-muted-foreground">
              New Password
            </Label>
            <div className="flex flex-col gap-3 sm:flex-row">
              <Input
                id="new-pw"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="At least 8 characters"
                minLength={8}
                className="text-xs bg-background"
              />
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={updatePassword}
                className="gap-1.5 shrink-0"
              >
                <Check className="size-3.5" />
                <span>Update Password</span>
              </Button>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}

function Preference({
  title,
  detail,
  defaultChecked = false,
}: {
  title: string;
  detail: string;
  defaultChecked?: boolean;
}) {
  const [checked, setChecked] = useState(defaultChecked);

  return (
    <div className="flex items-center justify-between gap-5 py-4">
      <div className="space-y-0.5 max-w-xl">
        <p className="text-xs font-bold text-primary">{title}</p>
        <p className="text-[11px] leading-relaxed text-muted-foreground">{detail}</p>
      </div>
      <Switch
        checked={checked}
        onCheckedChange={(value) => {
          setChecked(value);
          toast.success("Notification preference updated.");
        }}
        aria-label={title}
      />
    </div>
  );
}
