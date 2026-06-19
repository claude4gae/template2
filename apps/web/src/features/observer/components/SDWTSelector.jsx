// src/features/observer/components/drilldown/SDWTSelector.jsx
import React from "react";
import { useSDWT } from "../hooks/useLineQueries";
import { LoadingSpinner } from "./Loaders";

/**
 * SDWT 드롭다운
 */
export default function SDWTSelector({ lineId, sdwtId, setSdwtId }) {
  const { data: sdwts = [], isLoading } = useSDWT(lineId);

  if (!lineId)
    return (
      <select
        disabled
        className="w-full h-8 rounded-lg border border-border bg-muted px-3 py-1.5 text-xs text-muted-foreground"
      >
        <option>SDWT 선택…</option>
      </select>
    );

  if (isLoading) return <LoadingSpinner />;

  return (
    <select
      value={sdwtId}
      onChange={(e) => setSdwtId(e.target.value)}
      className="w-full h-8 rounded-lg border border-border bg-card px-3 py-1.5 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-background disabled:opacity-60"
    >
      <option value="">SDWT 선택…</option>
      {sdwts.map((s) => (
        <option key={s.id} value={s.id}>
          {s.name}
        </option>
      ))}
    </select>
  );
}
