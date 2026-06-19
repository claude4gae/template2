import React from "react";

export default function ObserverEmptyState({
  title,
  message,
  detail,
  bodyClassName = "h-[74px]",
  headerNote,
}) {
  return (
    <div className="observer-container relative">
      {(title || headerNote) && (
        <div className="mb-1 flex items-center justify-between">
          {title ? (
            <h3 className="text-sm font-semibold text-foreground">{title}</h3>
          ) : (
            <div />
          )}
          {headerNote ? (
            <span className="text-xs text-muted-foreground">{headerNote}</span>
          ) : null}
        </div>
      )}
      <div
        className={`flex items-center justify-center rounded border border-border bg-muted px-3 text-center ${bodyClassName}`}
      >
        <p className="text-sm text-muted-foreground">
          {message}
          {detail ? <span className="block text-xs">{detail}</span> : null}
        </p>
      </div>
    </div>
  );
}
