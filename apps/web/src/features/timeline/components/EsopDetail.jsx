import React from "react";
import { ExternalLink, ImageIcon } from "lucide-react";
import Field from "./Field";

function getDefectImageUrls(item) {
  if (!Array.isArray(item?.imageUrls)) return [];
  return item.imageUrls
    .map((url) => (typeof url === "string" ? url.trim() : ""))
    .filter(Boolean);
}

function DefectMapLink({ item, index }) {
  const imageUrls = getDefectImageUrls(item);
  const label = item.label || `Defect Map ${index + 1}`;

  if (!imageUrls.length) {
    return (
      <a
        href={item.url}
        className="inline-flex items-center gap-1 text-primary underline break-all transition-colors hover:text-primary/80 focus:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
        target="_blank"
        rel="noopener noreferrer"
        title={item.url}
        aria-label={`${label} URL 새 탭에서 열기`}
      >
        {label}
        <ExternalLink className="h-3.5 w-3.5 shrink-0" />
      </a>
    );
  }

  if (imageUrls.length === 1) {
    return (
      <a
        href={imageUrls[0]}
        className="inline-flex items-center gap-1 text-primary underline break-all transition-colors hover:text-primary/80 focus:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
        target="_blank"
        rel="noopener noreferrer"
        title={imageUrls[0]}
        aria-label={`${label} 이미지 새 탭에서 열기`}
      >
        <ImageIcon className="h-3.5 w-3.5 shrink-0" />
        {label}
      </a>
    );
  }

  return (
    <div className="flex flex-wrap items-center gap-1.5">
      <span className="font-medium text-foreground">{label}</span>
      {imageUrls.map((imageUrl, imageIndex) => (
        <a
          key={`${imageUrl}-${imageIndex}`}
          href={imageUrl}
          className="inline-flex items-center gap-1 text-primary underline transition-colors hover:text-primary/80 focus:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          target="_blank"
          rel="noopener noreferrer"
          title={imageUrl}
          aria-label={`${label} 이미지 ${imageIndex + 1} 새 탭에서 열기`}
        >
          <ImageIcon className="h-3.5 w-3.5 shrink-0" />
          {imageIndex + 1}
        </a>
      ))}
    </div>
  );
}

function DefectMapLinks({ maps }) {
  if (!Array.isArray(maps) || maps.length === 0) return null;

  return (
    <>
      <div className="font-semibold text-foreground col-span-2">
        Defect Map
      </div>
      <div className="col-span-2 flex flex-col gap-1">
        {maps.map((item, index) => (
          <DefectMapLink
            key={`${item.url}-${index}`}
            item={item}
            index={index}
          />
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
