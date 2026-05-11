// Number, percent, money, and date formatting helpers.

export function fmtMoney(v, digits = 2) {
  if (v == null) return '·'
  const n = Number(v)
  return n.toLocaleString('en-US', { minimumFractionDigits: digits, maximumFractionDigits: digits })
}

export function fmtMoneyCompact(v) {
  if (v == null) return '·'
  const n = Number(v)
  if (Math.abs(n) >= 1000) {
    return `$${Math.round(n).toLocaleString('en-US')}`
  }
  return `$${n.toFixed(2)}`
}

export function fmtPct(v, digits = 1) {
  if (v == null) return '·'
  const n = Number(v)
  const sign = n > 0 ? '+' : ''
  return `${sign}${n.toFixed(digits)}%`
}

export function pnlClass(v) {
  if (v == null) return 'text-slate-300'
  const n = Number(v)
  if (n > 0) return 'text-accent-green'
  if (n < 0) return 'text-accent-red'
  return 'text-slate-300'
}

// Days until a date. Negative = past, 0 = today, positive = future.
export function daysUntil(dateStr) {
  if (!dateStr) return null
  const target = new Date(dateStr + 'T00:00:00')
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const ms = target - today
  return Math.round(ms / 86400000)
}

// Earnings urgency bucket for the dot color in the legend and the strip.
export function earningsUrgency(dateStr, reported) {
  if (reported) return null
  const days = daysUntil(dateStr)
  if (days == null || days < 0) return null
  if (days <= 3) return 'red'
  if (days <= 7) return 'orange'
  if (days <= 14) return 'yellow'
  return null
}
