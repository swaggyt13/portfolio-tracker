// Legend strip under the header. Tier dots on the left, earnings urgency on the right.

const TIERS = [
  { code: 'T1', label: 'T1 · Semi & AI Core', color: 'bg-emerald-400' },
  { code: 'T2', label: 'T2 · Energy & Materials', color: 'bg-orange-400' },
  { code: 'T3', label: 'T3 · Industrials', color: 'bg-blue-400' },
  { code: 'T4', label: 'T4 · Healthcare', color: 'bg-purple-400' },
  { code: 'T5', label: 'T5 · Other', color: 'bg-slate-400' },
]

const URGENCIES = [
  { code: 'red', label: 'Earnings ≤ 3d', color: 'bg-red-500' },
  { code: 'orange', label: 'Earnings ≤ 7d', color: 'bg-orange-500' },
  { code: 'yellow', label: 'Earnings ≤ 14d', color: 'bg-yellow-400' },
]

function Item({ color, label, shape = 'circle' }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-xs text-muted">
      <span className={`${color} ${shape === 'circle' ? 'rounded-full w-2 h-2' : 'rounded-sm w-2.5 h-2.5'}`} />
      {label}
    </span>
  )
}

export default function Legend() {
  return (
    <div className="flex flex-wrap gap-x-6 gap-y-2 py-3 border-b border-line">
      {TIERS.map((t) => (
        <Item key={t.code} color={t.color} label={t.label} />
      ))}
      <span className="text-line">|</span>
      {URGENCIES.map((u) => (
        <Item key={u.code} color={u.color} label={u.label} shape="square" />
      ))}
    </div>
  )
}
