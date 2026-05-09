import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  XAxis,
  YAxis,
} from "recharts"

import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart"
import {
  DEFAULT_BIN,
  GRID_OPACITY,
  GRID_STROKE,
  THEME_LINE_COLOR,
} from "../../utils/lineHistoryConfig"
import {
  formatAxisLabelByBin,
  formatTooltipLabelByBin,
} from "../../utils/lineHistoryTransforms"

function EmptyChartState({ children }) {
  return (
    <div className="flex h-full min-h-[180px] items-center justify-center rounded-lg border border-dashed text-xs text-muted-foreground">
      {children}
    </div>
  )
}

function KstTooltipContent(props) {
  const { label, bin = DEFAULT_BIN, ...rest } = props
  const formattedLabel = formatTooltipLabelByBin(label, bin)
  return <ChartTooltipContent {...rest} label={formattedLabel} />
}

function LineChartFrame({
  config,
  data,
  binMode,
  tickMargin,
  children,
}) {
  return (
    <ChartContainer config={config} className="flex-1 min-h-[180px]">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 16, right: 8, left: 0, bottom: 56 }}>
          <CartesianGrid
            horizontal
            vertical={false}
            stroke={GRID_STROKE}
            strokeDasharray="4 4"
            strokeOpacity={GRID_OPACITY}
          />
          <XAxis
            dataKey="date"
            tickFormatter={(value) => formatAxisLabelByBin(value, binMode)}
            tickMargin={tickMargin}
            minTickGap={12}
            angle={-45}
            textAnchor="end"
            height={tickMargin > 12 ? 56 : 60}
            tick={{ fontSize: 15 }}
          />
          <YAxis allowDecimals={false} width={64} />
          <ChartTooltip
            isAnimationActive={false}
            content={(props) => <KstTooltipContent {...props} bin={binMode} />}
          />
          {children}
        </LineChart>
      </ResponsiveContainer>
    </ChartContainer>
  )
}

export function LineHistoryMetricChart({
  hasMetricData = true,
  metricUnavailableText,
  totalUnavailableText,
  breakdownSeries,
  totalsData,
  totalsConfigEntry,
  totalsDataKey,
  hasTotalsData,
  hasFilterSelection,
  binMode,
  tickMargin = 12,
  fallbackColor = "var(--chart-1)",
}) {
  if (!hasMetricData) {
    return <EmptyChartState>{metricUnavailableText}</EmptyChartState>
  }

  const showBreakdown =
    hasFilterSelection && Array.isArray(breakdownSeries?.data) && breakdownSeries.data.length > 0

  if (showBreakdown) {
    return (
      <LineChartFrame
        config={breakdownSeries.config}
        data={breakdownSeries.data}
        binMode={binMode}
        tickMargin={tickMargin}
      >
        {breakdownSeries.seriesKeys.map((seriesKey) => (
          <Line
            key={seriesKey}
            type="monotone"
            dataKey={seriesKey}
            name={breakdownSeries.config?.[seriesKey]?.label ?? seriesKey}
            stroke={breakdownSeries.config?.[seriesKey]?.color ?? fallbackColor}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 5 }}
          />
        ))}
      </LineChartFrame>
    )
  }

  if (!hasTotalsData) {
    return <EmptyChartState>{totalUnavailableText}</EmptyChartState>
  }

  const totalsConfig = {
    [totalsDataKey]: hasFilterSelection
      ? totalsConfigEntry
      : { ...totalsConfigEntry, color: THEME_LINE_COLOR },
  }

  return (
    <LineChartFrame
      config={totalsConfig}
      data={totalsData}
      binMode={binMode}
      tickMargin={tickMargin}
    >
      <Line
        type="monotone"
        dataKey={totalsDataKey}
        name={totalsConfig[totalsDataKey].label}
        stroke={totalsConfig[totalsDataKey].color}
        strokeWidth={2}
        dot={false}
        activeDot={{ r: 5 }}
      />
    </LineChartFrame>
  )
}
