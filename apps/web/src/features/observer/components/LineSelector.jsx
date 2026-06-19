// src/features/observer/components/drilldown/LineSelector.jsx
import React from "react";
import { useLines } from "../hooks/useLineQueries";
import { LoadingSpinner } from "./Loaders";

/**
 * 라인 목록 드롭다운
 */
export default function LineSelector({ lineId, setLineId }) {
  const { data: lines = [], isLoading } = useLines();

  if (isLoading) return <LoadingSpinner />;

  return (
    <select
      value={lineId}
      onChange={(e) => setLineId(e.target.value)}
      className="w-full h-8 rounded-lg border border-border bg-card px-3 py-1.5 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-background"
    >
      <option value="">라인 선택…</option>
      {lines.map((l) => (
        <option key={l.id} value={l.id}>
          {l.name}
        </option>
      ))}
    </select>
  );
}
