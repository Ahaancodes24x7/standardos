import { createFileRoute } from "@tanstack/react-router";
import { Bell, Check, KeyRound, Save } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { toast } from "sonner";
import { useAuth } from "@/contexts/auth-context";
import { updatePassword as updatePasswordRequest, updateProfile } from "@/services/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";

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
      toast.error("Use at least 8 characters.");
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
    <div className="reveal max-w-4xl">
      <header>
        <p className="eyebrow">Workspace / Settings</p>
        <h1 className="page-title mt-3">Settings</h1>
        <p className="mt-4 text-muted-foreground">
          Manage your identity, organization, and review notifications.
        </p>
      </header>
      <section className="mt-12 border-t border-border pt-7">
        <h2 className="text-xl font-bold text-primary">Profile</h2>
        <form onSubmit={saveProfile} className="mt-6 grid gap-5 sm:grid-cols-2">
          <div className="grid gap-2">
            <Label htmlFor="settings-name">Full name</Label>
            <Input
              id="settings-name"
              value={name}
              onChange={(event) => setName(event.target.value)}
              required
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="settings-org">Organization</Label>
            <Input
              id="settings-org"
              value={organization}
              onChange={(event) => setOrganization(event.target.value)}
              required
            />
          </div>
          <div className="sm:col-span-2">
            <Button type="submit" disabled={saving}>
              <Save />
              {saving ? "Saving…" : "Save profile"}
            </Button>
          </div>
        </form>
      </section>
      <section className="mt-12 border-t border-border pt-7">
        <div className="flex items-center gap-3">
          <Bell className="size-5 text-accent-foreground" />
          <h2 className="text-xl font-bold text-primary">Notifications</h2>
        </div>
        <div className="mt-5 divide-y divide-border">
          <Preference
            title="Standards amendments"
            detail="Alert me when a mapped standard changes."
            defaultChecked
          />
          <Preference
            title="Compliance review reminders"
            detail="Notify me about unresolved high-severity findings."
            defaultChecked
          />
          <Preference
            title="Analysis completion"
            detail="Notify me when a long-running analysis completes."
          />
        </div>
      </section>
      <section className="mt-12 border-t border-border pt-7">
        <div className="flex items-center gap-3">
          <KeyRound className="size-5 text-accent-foreground" />
          <h2 className="text-xl font-bold text-primary">Password</h2>
        </div>
        {isDemo ? (
          <p className="mt-4 text-sm text-muted-foreground">
            Password changes are unavailable in the demonstration workspace.
          </p>
        ) : (
          <div className="mt-5 flex max-w-xl flex-col gap-3 sm:flex-row">
            <Input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="New password"
              minLength={8}
            />
            <Button type="button" variant="outline" onClick={updatePassword}>
              <Check />
              Update password
            </Button>
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
    <div className="flex items-center gap-5 py-5">
      <div className="flex-1">
        <p className="font-semibold text-primary">{title}</p>
        <p className="mt-1 text-sm text-muted-foreground">{detail}</p>
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
