import { groupConfig } from "./observerMeta";

export function makeGroupLabel(type, title) {
  // showLegend 파라미터 제거하고 항상 기본 라벨만 반환
  return `<div style="width:240px">${title}</div>`;
}

export function makeGroupLegend(type) {
  const EMOJI = {
    RUN: "🟦RUN ",
    IDLE: "🟩IDLE ",
    PM: "🟨PM ",
    DOWN: "🟥DOWN ",
    OPEN: "🟦OPEN ",
    CLOSE: "🟥CLOSE ",
    ALARM: "🟥ALARM ",
    WARN: "🟧WARN ",
    CBM: "🟦CBM ",
    NSP: "🟩NSP ",
    ISSUED: "🟦ISSUED ",
    CLOSED: "🟪CLOSED ",
  };
  const config = groupConfig[type];
  if (!config) return `<div style="width:240px"></div>`;
  const legendHtml = Object.keys(config.stateClasses || {})
    .map((state) => `<span>${EMOJI[state] || "▪️"}</span>`)
    .join(" ");
  return `<div style="width:240px;">${legendHtml}</div>`;
}

export function makeTipGroupLabel(process, step, ppid) {
  // showLegend 파라미터 제거하고 PPID만 표시
  const displayText = `<div class="tip-group-label-simple">${
    ppid || "N/A"
  }</div>`;
  return `<div style="width:240px">${displayText}</div>`;
}
