// src/features/observer/components/BaseObserver.jsx
import React, { useRef } from "react";
import moment from "moment";
import "moment/locale/ko";
import { useVisObserver } from "../hooks/useVisObserver";

const KOREAN_OBSERVER_LOCALE = {
  current: "현재",
  time: "시간",
  deleteSelected: "선택 항목 삭제",
};

const toKoreanMoment = (date) => moment(date).locale("ko");

const KOREAN_AXIS_FORMAT = {
  minorLabels: {
    millisecond: "HH:mm:ss.SSS",
    second: "HH:mm:ss",
    minute: "HH:mm",
    hour: "HH:mm",
    weekday: "MM/DD",
    day: "MM/DD",
    month: "MM/DD",
    year: "YY",
  },
  majorLabels: {
    millisecond: "MM월 DD일",
    second: "MM월 DD일",
    minute: "MM월 DD일",
    hour: "MM월 DD일",
    weekday: "MM월 DD일",
    day: "YY년 MM월",
    month: "YYYY",
    year: "",
  },
};

/**
 * 재사용 가능한 기본 Observer 컴포넌트
 * @param {Object} props
 * @param {Array} props.groups - Observer 그룹 정의
 * @param {Array} props.items - Observer 아이템
 * @param {Object} props.options - vis-timeline 옵션
 * @param {string} props.title - Observer 제목
 * @param {ReactNode} props.headerExtra - 헤더 추가 요소
 * @param {boolean} props.showTimeAxis - x축 표시 여부
 */
export default function BaseObserver({
  groups,
  items,
  options = {},
  title,
  headerExtra,
  className = "",
  style = {},
  showTimeAxis = true,
  height,
  minHeight,
  maxHeight,
}) {
  const containerRef = useRef(null);

  const mergedOptions = {
    margin: { item: 0, axis: 0 },
    groupOrder: "order",
    selectable: true,
    locale: "ko",
    locales: { ko: KOREAN_OBSERVER_LOCALE },
    moment: toKoreanMoment,
    verticalScroll:
      options.verticalScroll !== undefined ? options.verticalScroll : true,
    tooltip: {
      followMouse: true,
      overflowMethod: "flip",
    },
    showMajorLabels: showTimeAxis,
    showMinorLabels: showTimeAxis,
    format: KOREAN_AXIS_FORMAT,
    align: "center",
    orientation: {
      item: "top",
    },
    ...(height !== undefined && { height }),
    ...(minHeight !== undefined && { minHeight }),
    ...(maxHeight !== undefined && { maxHeight }),
    ...options,
  };

  useVisObserver({
    containerRef,
    groups,
    items,
    options: mergedOptions,
  });

  // 동적 스타일 계산
  const containerStyle = {
    ...style,
    ...(mergedOptions.height ? { height: `${mergedOptions.height}px` } : {}),
  };

  return (
    <div
      className={`observer-container relative ${className} ${!showTimeAxis ? "no-time-axis" : ""
        }`}
    >
      {(title || headerExtra) && (
        <div className="flex items-center justify-between">
          {title && (
            <h3 className="text-sm font-semibold text-foreground">
              {title}
            </h3>
          )}
          {headerExtra}
        </div>
      )}

      <div ref={containerRef} className="observer" style={containerStyle} />
    </div>
  );
}
