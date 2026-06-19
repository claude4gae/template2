export const CHART_MARKER_SIZE = 8

export const STATUS_ORDER = ['Normal (Ref)', 'Warning', 'High Risk Chamber']

export const STATUS_MARKER = {
  'High Risk Chamber': {
    label:  'High Risk',
    color:  '#dc2626',
    symbol: 'circle',
    filled: true,
  },
  'Warning': {
    label:  'Warning',
    color:  '#ea580c',
    symbol: 'circle-open',
    filled: false,
  },
  'Normal (Ref)': {
    label:  'Normal',
    color:  '#4b5563',
    symbol: 'circle-open',
    filled: false,
  },
}

export const EQC_TIME_STATUS_MARKER = {
  'Normal (Ref)': {
    label:  'Normal',
    color:  '#4b5563',
    symbol: 'circle-open',
    filled: false,
  },
  'Warning': {
    label:  'Warning',
    color:  '#ea580c',
    symbol: 'circle',
    filled: true,
  },
  'High Risk Chamber': {
    label:  'High Risk',
    color:  '#dc2626',
    symbol: 'star',
    filled: true,
  },
}
