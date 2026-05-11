// Small badge next to the next earnings date showing relative urgency.

import { daysUntil } from '../utils/format.js'

export default function EarningsBadge({ dateStr, reported }) {
  if (!dateStr) {
    return <span className="text-muted text-xs">·</span>
  }

  if (reported) {
    return <span className="text-muted text-xs">reported</span>
  }

  const days = daysUntil(dateStr)
  if (days == null) return <span className="text-xs font-mono">{dateStr}</span>

  let badge = null
  if (days < 0) {
    badge = <span className="text-muted text-[10px]">past</span>
  } else if (days === 0) {
    badge = (
      <span className="text-[10px] font-mono px-1 py-0.5 rounded bg-red-500/30 text-red-300">
        TODAY
      </span>
    )
  } else if (days <= 3) {
    badge = (
      <span className="text-[10px] font-mono px-1 py-0.5 rounded bg-red-500/25 text-red-300">
        {days}d
      </span>
    )
  } else if (days <= 7) {
    badge = (
      <span className="text-[10px] font-mono px-1 py-0.5 rounded bg-orange-500/25 text-orange-300">
        {days}d
      </span>
    )
  } else if (days <= 14) {
    badge = (
      <span className="text-[10px] font-mono px-1 py-0.5 rounded bg-yellow-500/25 text-yellow-300">
        {days}d
      </span>
    )
  }

  return (
    <span className="inline-flex items-center gap-1.5 font-mono text-xs">
      <span className="text-slate-300">{dateStr}</span>
      {badge}
    </span>
  )
}
