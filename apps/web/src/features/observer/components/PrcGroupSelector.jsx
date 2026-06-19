// src/features/observer/components/drilldown/PrcGroupSelector.jsx
import React from "react";
import { usePrcGroups } from "../hooks/useLineQueries";
import { LoadingSpinner } from "./Loaders";

/**
 * PRC Group 드롭다운
 */
export default function PrcGroupSelector({
  lineId,
  sdwtId,
  prcGroup,
  setPrcGroup,
}) {
  const { data: prcGroups = [], isLoading } = usePrcGroups(lineId, sdwtId);

  if (!lineId || !sdwtId)
    return (
      <select
        disabled
        className="w-full h-8 rounded-lg border border-border bg-muted px-3 py-1.5 text-xs text-muted-foreground"
      >
        <option>PRC Group 선택…</option>
      </select>
    );

  if (isLoading) return <LoadingSpinner />;

  return (
    <select
      value={prcGroup}
      onChange={(e) => setPrcGroup(e.target.value)}
      className="w-full h-8 rounded-lg border border-border bg-card px-3 py-1.5 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-background disabled:opacity-60"
      disabled={prcGroups.length === 0}
    >
      <option value="">PRC Group 선택…</option>
      {prcGroups.map((p) => (
        <option key={p.id} value={p.id}>
          {p.name}
        </option>
      ))}
    </select>
  );
}
