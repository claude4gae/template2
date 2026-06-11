import { RefreshCw, Search } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { cn } from "@/lib/utils"

import { hasRequiredPmFilters, normalizeOptions } from "../utils/format"

function Field({ id, label, children }) {
  return (
    <div className="grid min-w-0 gap-1.5">
      <Label htmlFor={id} className="text-xs font-medium text-muted-foreground">
        {label}
      </Label>
      {children}
    </div>
  )
}

function TextInput({ id, value, onChange, list, placeholder }) {
  return (
    <Input
      id={id}
      value={value}
      list={list}
      placeholder={placeholder}
      onChange={(event) => onChange(event.target.value)}
      className="h-9 bg-background"
    />
  )
}

function OptionList({ id, values }) {
  const options = normalizeOptions(values).slice(0, 200)
  if (!options.length) return null
  return (
    <datalist id={id}>
      {options.map((value) => (
        <option key={value} value={value} />
      ))}
    </datalist>
  )
}

export function PmComparisonFilterBar({
  form,
  meta,
  isMetaLoading,
  isResultFetching,
  onFormChange,
  onSubmit,
  onRefreshMeta,
}) {
  const canSubmit = hasRequiredPmFilters(form) && !isResultFetching

  const setField = (key, value) => {
    onFormChange({ ...form, [key]: value })
  }

  const submit = (event) => {
    event.preventDefault()
    if (!canSubmit) return
    onSubmit()
  }

  return (
    <section className="shrink-0 border-b bg-card">
      <form onSubmit={submit} className="grid gap-3 px-4 py-3 md:px-6">
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-[repeat(6,minmax(0,1fr))_auto]">
          <Field id="pm-line-id" label="Line ID">
            <TextInput
              id="pm-line-id"
              value={form.lineId}
              list="pm-line-options"
              placeholder="LINE"
              onChange={(value) => setField("lineId", value)}
            />
          </Field>
          <Field id="pm-eqp-id" label="EQP ID">
            <TextInput
              id="pm-eqp-id"
              value={form.eqpId}
              list="pm-eqp-options"
              placeholder="EQP"
              onChange={(value) => setField("eqpId", value)}
            />
          </Field>
          <Field id="pm-timestamp" label="PM 기준 시점">
            <TextInput
              id="pm-timestamp"
              value={form.pmTimestamp}
              list="pm-date-options"
              placeholder="PM 날짜"
              onChange={(value) => setField("pmTimestamp", value)}
            />
          </Field>
          <Field id="pm-before-hours" label="Before hours">
            <Input
              id="pm-before-hours"
              type="number"
              min="0.1"
              max="720"
              step="0.5"
              value={form.beforeHours}
              onChange={(event) => setField("beforeHours", event.target.value)}
              className="h-9 bg-background"
            />
          </Field>
          <Field id="pm-after-hours" label="After hours">
            <Input
              id="pm-after-hours"
              type="number"
              min="0.1"
              max="720"
              step="0.5"
              value={form.afterHours}
              onChange={(event) => setField("afterHours", event.target.value)}
              className="h-9 bg-background"
            />
          </Field>
          <Field id="pm-limit" label="Trend limit">
            <Input
              id="pm-limit"
              type="number"
              min="50"
              max="5000"
              step="50"
              value={form.limit}
              onChange={(event) => setField("limit", event.target.value)}
              className="h-9 bg-background"
            />
          </Field>
          <div className="flex items-end gap-2">
            <Button type="submit" disabled={!canSubmit} className="h-9">
              <Search className="size-4" />
              조회
            </Button>
            <Button type="button" variant="outline" size="icon" onClick={onRefreshMeta} disabled={isMetaLoading}>
              <RefreshCw className={cn("size-4", isMetaLoading && "animate-spin")} />
              <span className="sr-only">메타데이터 새로고침</span>
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-[repeat(7,minmax(0,1fr))]">
          <Field id="pm-fdc-bin" label="FDC bin">
            <TextInput id="pm-fdc-bin" value={form.fdcBin} list="pm-fdc-bin-options" onChange={(value) => setField("fdcBin", value)} />
          </Field>
          <Field id="pm-ppid" label="PPID">
            <TextInput id="pm-ppid" value={form.ppid} list="pm-ppid-options" onChange={(value) => setField("ppid", value)} />
          </Field>
          <Field id="pm-recipe-id" label="Recipe ID">
            <TextInput id="pm-recipe-id" value={form.recipeId} list="pm-recipe-options" onChange={(value) => setField("recipeId", value)} />
          </Field>
          <Field id="pm-trace-params" label="Trace params">
            <TextInput
              id="pm-trace-params"
              value={form.traceParamNames}
              list="pm-trace-param-options"
              placeholder="comma separated"
              onChange={(value) => setField("traceParamNames", value)}
            />
          </Field>
          <Field id="pm-dt-values" label="dt values">
            <TextInput
              id="pm-dt-values"
              value={form.dtValues}
              list="pm-dt-options"
              placeholder="comma separated"
              onChange={(value) => setField("dtValues", value)}
            />
          </Field>
          <Field id="pm-trace-source" label="Trace source">
            <TextInput id="pm-trace-source" value={form.traceDataSource} onChange={(value) => setField("traceDataSource", value)} />
          </Field>
          <Field id="pm-oes-source" label="OES source">
            <TextInput id="pm-oes-source" value={form.oesDataSource} onChange={(value) => setField("oesDataSource", value)} />
          </Field>
        </div>

        <div className="flex items-center justify-between gap-3 text-xs text-muted-foreground">
          <div className="flex min-w-0 flex-wrap items-center gap-2">
            <Badge variant="outline">root: PM_COMPARISON_DATA_ROOT</Badge>
            <Badge variant="outline">pattern: NPW + SP(PW)</Badge>
            <Badge variant="secondary">trace: {form.traceDataSource || "trace"}</Badge>
            <Badge variant="secondary">oes: {form.oesDataSource || "oes"}</Badge>
          </div>
          <span>{isResultFetching ? "조회 중입니다." : "Line ID, EQP ID, PM 기준 시점은 필수입니다."}</span>
        </div>
      </form>

      <OptionList id="pm-line-options" values={meta?.lineIds} />
      <OptionList id="pm-eqp-options" values={meta?.eqpIds} />
      <OptionList id="pm-date-options" values={meta?.pmDates} />
      <OptionList id="pm-fdc-bin-options" values={meta?.fdcBins} />
      <OptionList id="pm-ppid-options" values={meta?.ppids} />
      <OptionList id="pm-recipe-options" values={meta?.recipeIds} />
      <OptionList id="pm-trace-param-options" values={meta?.traceParamNames} />
      <OptionList id="pm-dt-options" values={meta?.dtValues} />
    </section>
  )
}
