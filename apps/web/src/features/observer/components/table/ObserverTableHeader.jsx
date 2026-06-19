import React from "react";
import { observerTableColumnWidths } from "./observerTableColumns";

export default function ObserverTableHeader() {
  return (
    <div className="sticky top-0 z-10 bg-muted text-muted-foreground">
      <div className="flex text-xs font-semibold">
        <div
          style={{ width: `${observerTableColumnWidths.time}px` }}
          className="px-2 py-2 text-center flex-shrink-0"
        >
          Time
        </div>
        <div
          style={{ width: `${observerTableColumnWidths.logType}px` }}
          className="px-2 py-2 text-center flex-shrink-0"
        >
          LogType
        </div>
        <div
          style={{ width: `${observerTableColumnWidths.changeType}px` }}
          className="px-2 py-2 text-center flex-shrink-0"
        >
          ChangeType
        </div>
        <div
          style={{ width: `${observerTableColumnWidths.operator}px` }}
          className="px-2 py-2 text-center flex-shrink-0"
        >
          Operator
        </div>
        <div
          style={{ width: `${observerTableColumnWidths.duration}px` }}
          className="px-2 py-2 text-center flex-shrink-0"
        >
          Duration
        </div>
        <div
          style={{ width: `${observerTableColumnWidths.url}px` }}
          className="px-2 py-2 text-center flex-shrink-0"
        >
          URL
        </div>
      </div>
    </div>
  );
}
