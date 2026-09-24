import { cn } from "@/lib/utils";
import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

interface MetricCardProps {
  label: string;
  value: string | number;
  subtitle?: string;
  icon?: LucideIcon;
  trend?: {
    value: string;
    positive?: boolean;
    neutral?: boolean;
  };
  badge?: ReactNode;
  className?: string;
}

export function MetricCard({
  label,
  value,
  subtitle,
  icon: Icon,
  trend,
  badge,
  className,
}: MetricCardProps) {
  return (
    <div
      className={cn(
        "intel-card intel-card-hover relative flex flex-col justify-between p-5 sm:p-6",
        className,
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <p className="text-xs font-bold uppercase tracking-[0.1em] text-muted-foreground">
          {label}
        </p>
        {Icon && (
          <span className="grid size-9 shrink-0 place-items-center rounded-lg border border-border/80 bg-background/80 text-accent-foreground shadow-xs">
            <Icon className="size-4.5" />
          </span>
        )}
      </div>

      <div className="mt-4 flex items-baseline justify-between gap-3">
        <div className="text-3xl font-extrabold tracking-tight text-primary sm:text-4xl">
          {value}
        </div>
        {badge}
      </div>

      {(subtitle || trend) && (
        <div className="mt-3 flex items-center justify-between gap-2 border-t border-border/40 pt-2.5 text-xs text-muted-foreground">
          {subtitle && <span className="truncate">{subtitle}</span>}
          {trend && (
            <span
              className={cn(
                "ml-auto shrink-0 font-semibold",
                trend.neutral
                  ? "text-muted-foreground"
                  : trend.positive
                    ? "text-success-foreground"
                    : "text-destructive",
              )}
            >
              {trend.value}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
