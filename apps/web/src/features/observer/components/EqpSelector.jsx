// src/features/observer/components/drilldown/EqpSelector.jsx
import React from "react";
import { useEquipments } from "../hooks/useLineQueries";
import { LoadingSpinner } from "./Loaders";

/**
 * EQP 드롭다운
 */
export default function EqpSelector({
  lineId,
  sdwtId,
  prcGroup,
  eqpId,
  setEqpId,
}) {
  // 데이터·상태 가져오기 - prcGroup 추가
  const { data: eqps = [], isLoading } = useEquipments(
    lineId,
    sdwtId,
    prcGroup
  );

  // Line, SDWT, PRC Group 모두 선택해야 활성화
  if (!lineId || !sdwtId || !prcGroup)
    return (
      <select
        disabled
        className="w-full h-8 rounded-lg border border-border bg-muted px-3 py-1.5 text-xs text-muted-foreground"
      >
        <option>EQP 선택…</option>
      </select>
    );

  if (isLoading) return <LoadingSpinner />;

  return (
    <select
      value={eqpId}
      onChange={(e) => setEqpId(e.target.value)}
      className="w-full h-8 rounded-lg border border-border bg-card px-3 py-1.5 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-background disabled:opacity-60"
      disabled={eqps.length === 0}
    >
      <option value="">EQP 선택…</option>
      {eqps.map((e) => (
        <option key={e.id} value={e.id}>
          {e.name}
        </option>
      ))}
    </select>
  );
}
