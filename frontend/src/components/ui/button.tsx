import { cn } from "@/lib/utils";

type Variant = "primary" | "secondary" | "ghost" | "danger";

const variants: Record<Variant, string> = {
  primary:
    "bg-forge-primary-bg text-forge-primary-fg hover:opacity-90 shadow-sm",
  secondary:
    "border border-forge-border bg-forge-hover text-forge-text hover:bg-forge-accent-soft",
  ghost: "text-forge-muted hover:bg-forge-hover hover:text-forge-text",
  danger: "bg-red-500/15 text-red-600 dark:text-red-300 hover:bg-red-500/25",
};

export function Button({
  className,
  variant = "primary",
  loading,
  children,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; loading?: boolean }) {
  return (
    <button
      type="button"
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-all disabled:opacity-50",
        variants[variant],
        className
      )}
      disabled={loading || props.disabled}
      {...props}
    >
      {loading && (
        <span className="h-4 w-4 animate-spin rounded-full border-2 border-current/30 border-t-current" />
      )}
      {children}
    </button>
  );
}
