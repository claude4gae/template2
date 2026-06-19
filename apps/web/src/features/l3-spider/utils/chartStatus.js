export const CHART_MARKER_SIZE = 8

export const STATUS_ORDER = ['Normal (Ref)', 'Warning', 'High Risk Chamber']

export const STATUS_MARKER = {
  'High Risk Chamber': {
    label:  'High Risk',
    color:  'var(--destructive)',
    symbol: 'circle',
    filled: true,
  },
  'Warning': {
    label:  'Warning',
    color:  'var(--chart-4)',
    symbol: 'circle-open',
    filled: false,
  },
  'Normal (Ref)': {
    label:  'Normal',
    color:  'var(--muted-foreground)',
    symbol: 'circle-open',
    filled: false,
  },
}

export const EQC_TIME_STATUS_MARKER = {
  'Normal (Ref)': {
    label:  'Normal',
    color:  'var(--muted-foreground)',
    symbol: 'circle-open',
    filled: false,
  },
  'Warning': {
    label:  'Warning',
    color:  'var(--chart-4)',
    symbol: 'circle',
    filled: true,
  },
  'High Risk Chamber': {
    label:  'High Risk',
    color:  'var(--destructive)',
    symbol: 'star',
    filled: true,
  },
}
