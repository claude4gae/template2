// src/features/observer/components/ObserverSettings.jsx
import React from "react";
import { XMarkIcon } from "@heroicons/react/24/outline";
import LegendToggle from "./LegendToggle";
import TipTreeFilter from "./TipTreeFilter";

export default function ObserverSettings({
  isOpen,
  onClose,
  showLegend,
  selectedTipGroups,
  onLegendToggle,
  onTipFilterChange,
  tipLogs,
}) {
  if (!isOpen) return null;

  return (
    <div className="w-[320px] ml-2 max-h-full border border-border bg-card shadow-sm overflow-y-auto rounded-xl">
      <div className="p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-foreground">
            Observer 설정
          </h3>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        <div className="space-y-6">
          {/* Legend 설정 섹션 */}
          <div className="border-y border-border py-3">
            <div className="flex items-center justify-end">
              <LegendToggle showLegend={showLegend} onToggle={onLegendToggle} />
            </div>
          </div>

          {/* TIP 필터 섹션 */}
          {tipLogs && tipLogs.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-foreground mb-4">
                TIP 그룹 필터
              </h3>
              <TipTreeFilter
                tipLogs={tipLogs}
                selectedTipGroups={selectedTipGroups}
                onFilterChange={onTipFilterChange}
                inDrawer={true}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
