// src/features/observer/components/ShareButton.jsx
import React, { useState } from "react";

export default function ShareButton() {
  const [showToast, setShowToast] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);

  const handleShare = async () => {
    const url = window.location.href;

    try {
      if (navigator.share) {
        await navigator.share({
          title: "EQP Observer",
          text: "Observer 링크를 공유합니다",
          url: url,
        });
      } else {
        await navigator.clipboard.writeText(url);
        setShowToast(true);
        setTimeout(() => setShowToast(false), 3000);
      }
    } catch (err) {
      console.error("URL 공유 실패:", err);
      const textArea = document.createElement("textarea");
      textArea.value = url;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand("copy");
      document.body.removeChild(textArea);
      setShowToast(true);
      setTimeout(() => setShowToast(false), 3000);
    }
  };

  return (
    <>
      {/* 링크복사 버튼과 툴팁을 같은 기준점에 둡니다. */}
      <div className="relative inline-flex h-9 shrink-0 items-center">
        <button
          type="button"
          onClick={handleShare}
          aria-label="URL 복사"
          className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-border bg-card text-primary transition-colors hover:bg-muted hover:text-primary/80 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
          onMouseEnter={() => setShowTooltip(true)}
          onMouseLeave={() => setShowTooltip(false)}
          onFocus={() => setShowTooltip(true)}
          onBlur={() => setShowTooltip(false)}
        >
          <svg
            className="h-4 w-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
            />
          </svg>
        </button>

        {/* 툴팁 */}
        {showTooltip && (
          <div className="pointer-events-none absolute top-1/2 left-full ml-2 -translate-y-1/2 transform whitespace-nowrap rounded-md border border-border bg-popover px-2 py-1 text-xs text-popover-foreground shadow-sm">
            URL 복사
          </div>
        )}
      </div>

      {/* 토스트 메시지 */}
      {showToast && (
        <div className="fixed bottom-4 right-4 z-50 rounded-lg bg-primary px-4 py-2 text-primary-foreground shadow-lg animate-fade-in">
          URL이 클립보드에 복사되었습니다!
        </div>
      )}
    </>
  );
}
