import type { ReactNode } from "react";
import { MethodologyDialog } from "./methodology-dialog";

interface PageHeaderProps {
  eyebrow: string;
  title: string;
  description?: string;
  methodologyTitle?: string;
  methodologyContent?: ReactNode;
  children?: ReactNode;
}

export function PageHeader({
  eyebrow,
  title,
  description,
  methodologyTitle,
  methodologyContent,
  children,
}: PageHeaderProps) {
  return (
    <header className="relative flex flex-col gap-5 border-b border-border/70 pb-7 sm:flex-row sm:items-end sm:justify-between">
      <div className="max-w-3xl space-y-1.5">
        <div className="flex flex-wrap items-center gap-3">
          <p className="eyebrow">{eyebrow}</p>
          {methodologyContent ? (
            <MethodologyDialog title={methodologyTitle} size="sm">
              {methodologyContent}
            </MethodologyDialog>
          ) : null}
        </div>
        <h1 className="text-3xl font-extrabold tracking-tight text-primary sm:text-4xl">{title}</h1>
        {description && (
          <p className="text-sm leading-relaxed text-muted-foreground">{description}</p>
        )}
      </div>
      {children && <div className="flex flex-wrap items-center gap-2.5 shrink-0">{children}</div>}
    </header>
  );
}
