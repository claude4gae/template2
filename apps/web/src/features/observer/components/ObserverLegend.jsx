import React from "react";

export default function ObserverLegend({ items = [] }) {
  if (!items.length) return null;

  return (
    <div className="flex items-center gap-3 px-2">
      <div className="flex gap-3">
        {items.map(({ key, className, label }) => (
          <div key={key || label} className="flex items-center gap-1">
            <span aria-hidden className={`observer-legend-dot ${className}`} />
            <span className="text-xs text-muted-foreground">{label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
