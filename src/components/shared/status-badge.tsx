import { cn } from "@/lib/utils";
import type { FindingStatus, ReviewStatus, Severity } from "@/lib/contracts";
import {
  AlertTriangle,
  Award,
  CheckCircle2,
  Clock3,
  FileWarning,
  ShieldAlert,
  ShieldCheck,
} from "lucide-react";

interface StatusBadgeProps {
  status: FindingStatus | ReviewStatus | Severity | string;
  type?: "finding" | "review" | "severity" | "generic";
  size?: "sm" | "md";
  showIcon?: boolean;
  className?: string;
}

export function StatusBadge({
  status,
  type = "finding",
  size = "md",
  showIcon = true,
  className,
}: StatusBadgeProps) {
  const norm = String(status).toLowerCase();
  let badgeStyle = "badge-slate";
  let label = status;
  let Icon = null;

  if (type === "finding") {
    switch (norm) {
      case "verified":
        badgeStyle = "badge-emerald";
        label = "Verified";
        Icon = CheckCircle2;
        break;
      case "conflicting":
        badgeStyle = "badge-crimson";
        label = "Conflicting";
        Icon = AlertTriangle;
        break;
      case "missing":
        badgeStyle = "badge-amber";
        label = "Missing / Gap";
        Icon = FileWarning;
        break;
      case "outdated":
        badgeStyle = "badge-amber";
        label = "Outdated";
        Icon = Clock3;
        break;
      case "certification":
        badgeStyle = "badge-indigo";
        label = "Certification";
        Icon = Award;
        break;
    }
  } else if (type === "review") {
    switch (norm) {
      case "confirmed":
        badgeStyle = "badge-emerald";
        label = "Confirmed";
        Icon = ShieldCheck;
        break;
      case "dismissed":
        badgeStyle = "badge-slate";
        label = "Dismissed";
        Icon = null;
        break;
      case "open":
      default:
        badgeStyle = "badge-indigo";
        label = "Under Review";
        Icon = ShieldAlert;
        break;
    }
  } else if (type === "severity") {
    switch (norm) {
      case "high":
        badgeStyle = "badge-crimson";
        label = "High Priority";
        Icon = AlertTriangle;
        break;
      case "medium":
        badgeStyle = "badge-amber";
        label = "Medium";
        Icon = FileWarning;
        break;
      case "low":
        badgeStyle = "badge-indigo";
        label = "Low";
        Icon = CheckCircle2;
        break;
    }
  }

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 font-bold tracking-[0.04em] uppercase transition-colors",
        size === "sm" ? "rounded-md px-2 py-0.5 text-[10px]" : "rounded-md px-2.5 py-1 text-xs",
        badgeStyle,
        className,
      )}
    >
      {showIcon && Icon && <Icon className={size === "sm" ? "size-3" : "size-3.5"} />}
      <span>{label}</span>
    </span>
  );
}
