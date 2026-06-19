import React from "react";

export function LoadingSpinner({ label, size = "md" }) {
  const dimension = size === "sm" ? "h-4 w-4" : "h-8 w-8";

  return (
    <div className="flex flex-col items-center justify-center gap-2">
      <div
        className={`animate-spin rounded-full border-2 border-muted border-t-primary ${dimension}`}
      />
      {label ? (
        <span className="text-xs text-muted-foreground">
          {label}
        </span>
      ) : null}
    </div>
  );
}

export function PageLoader({ label = "Loading observer…" }) {
  return (
    <div className="flex items-center justify-center h-full min-h-[50vh]">
      <LoadingSpinner label={label} />
    </div>
  );
}
