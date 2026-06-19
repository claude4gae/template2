import React from "react";
import Field from "./Field";

function DefectMapLinks({ maps }) {
  if (!Array.isArray(maps) || maps.length === 0) return null;

  return (
    <>
      <div className="font-semibold text-foreground col-span-2">
        Defect Map
      </div>
      <div className="col-span-2 flex flex-col gap-1">
        {maps.map((item, index) => (
          <a
            key={`${item.url}-${index}`}
            href={item.url}
            className="text-primary underline break-all"
            target="_blank"
            rel="noopener noreferrer"
          >
            {item.label || item.url}
          </a>
        ))}
      </div>
    </>
  );
}

export default function EsopDetail({ log }) {
  return (
    <>
      <Field label="Log Type" value={log.logType} />
      <Field label="Sample Type" value={log.eventType} />
      <Field label="Lot ID" value={log.lotId} />
      <Field label="Status" value={log.status} />
      <Field label="Time" value={log.eventTime} />
      <Field label="Operator" value={log.operator} />
      <Field label="Line" value={log.lineId} />
      <Field label="EQP-CB" value={log.eqpCb} />
      <Field label="Comment" value={log.comment} className="col-span-2" />
      <DefectMapLinks maps={log.defectMaps} />
    </>
  );
}
