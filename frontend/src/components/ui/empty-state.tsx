import type { LucideIcon } from "lucide-react";
import { Database } from "lucide-react";

export function EmptyState({
  title,
  description,
  action,
  icon: Icon = Database,
}: {
  title: string;
  description?: string;
  action?: React.ReactNode;
  icon?: LucideIcon;
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-forge-border py-16 text-center">
      <Icon className="mb-4 h-12 w-12 text-forge-muted/50" />
      <h3 className="text-lg font-medium text-forge-text">{title}</h3>
      {description && <p className="mt-2 max-w-md text-sm text-forge-muted">{description}</p>}
      {action && <div className="mt-6">{action}</div>}
    </div>
  );
}
