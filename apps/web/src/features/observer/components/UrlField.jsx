// src/features/observer/components/logDetail/UrlField.jsx
import React from "react";

/**
 * URL 필드 컴포넌트
 */
export default function UrlField({ url }) {
  if (!url) return null;

  return (
    <>
      <div className="font-semibold text-foreground">
        URL
      </div>
      <div>
        <a
          href={url}
          className="text-primary underline break-all"
          target="_blank"
          rel="noopener noreferrer"
        >
          {url}
        </a>
      </div>
    </>
  );
}
