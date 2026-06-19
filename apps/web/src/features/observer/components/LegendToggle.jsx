// src/features/observer/components/LegendToggle.jsx
import React from "react";

export default function LegendToggle({ showLegend, onToggle }) {
  return (
    <label className="inline-flex items-center cursor-pointer">
      <span className="mr-2 text-xs font-semibold text-foreground">
        Show Legend
      </span>
      <input
        type="checkbox"
        value=""
        className="sr-only peer"
        checked={showLegend}
        onChange={onToggle}
      />
      <div className="relative h-5 w-9 rounded-full bg-muted transition-colors peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/40 after:absolute after:start-[2px] after:top-[2px] after:h-4 after:w-4 after:rounded-full after:bg-background after:transition-all peer-checked:bg-primary peer-checked:after:translate-x-4"></div>
    </label>
  );
}
