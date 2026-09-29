import { cn } from "@/lib/utils";

export function Card({
  className,
  children,
  title,
  action,
}: {
  className?: string;
  children: React.ReactNode;
  title?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className={cn("glass-panel gradient-border p-5", className)}>
      {(title || action) && (
        <div className="mb-4 flex items-center justify-between">
          {title && <h3 className="text-sm font-semibold text-forge-text">{title}</h3>}
          {action}
        </div>
      )}
      {children}
    </div>
  );
}
