export const DIMENSION_OPTIONS = [
  { value: "sdwt_prod", label: "SDWT Prod" },
  { value: "process", label: "Process" },
  { value: "main_step", label: "Step" },
  { value: "ppid", label: "PPID" },
  { value: "sdwt", label: "SDWT" },
  { value: "user_sdwt", label: "User SDWT" },
]

export const DIMENSION_LABELS = DIMENSION_OPTIONS.reduce(
  (labels, option) => ({ ...labels, [option.value]: option.label }),
  {},
)

export const DIMENSION_ALIASES = {
  process: ["proc_id"],
  user_sdwt: ["user_sdwt_prod"],
  sdwt: ["sdwt_prod", "user_sdwt_prod"],
}

export const METRIC_OPTIONS = [
  { value: "rowCount", label: "진행 건수" },
  { value: "sendJiraCount", label: "Send Jira" },
]

export const METRIC_LABELS = METRIC_OPTIONS.reduce(
  (labels, option) => ({ ...labels, [option.value]: option.label }),
  {},
)

export const BIN_OPTIONS = [
  { value: "hour", label: "시간별" },
  { value: "day", label: "일별" },
  { value: "week", label: "주별" },
  { value: "month", label: "월별" },
]

export const BIN_LABELS = BIN_OPTIONS.reduce(
  (labels, option) => ({ ...labels, [option.value]: option.label }),
  {},
)

export const DEFAULT_BIN = BIN_OPTIONS[0].value

export const CATEGORY_COLORS = [
  "var(--chart-1)",
  "var(--chart-2)",
  "var(--chart-3)",
  "var(--chart-4)",
  "var(--chart-5)",
  "var(--primary)",
  "var(--secondary)",
  "var(--accent)",
  "var(--muted-foreground)",
  "var(--foreground)",
]

export const GRID_STROKE = "var(--border)"
export const GRID_OPACITY = 0.65
export const LEGEND_PRESET_COLORS = [
  ...CATEGORY_COLORS,
  "var(--primary-foreground)",
  "var(--secondary-foreground)",
]
export const THEME_LINE_COLOR = "var(--primary)"

export const HISTORY_LABELS = {
  titleSuffix: "Line E-SOP History",
  updated: "Updated",
}

export const totalsChartConfig = {
  rowCount: { label: "진행 건수", color: "var(--chart-1)" },
  sendJiraCount: { label: "Send Jira", color: "var(--chart-2)" },
}
