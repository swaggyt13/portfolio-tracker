// Tier badge styled by tier code. Five tier palette.

const TAG_STYLES = {
  T1: 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40',
  T2: 'bg-orange-500/20 text-orange-300 border border-orange-500/40',
  T3: 'bg-blue-500/20 text-blue-300 border border-blue-500/40',
  T4: 'bg-purple-500/20 text-purple-300 border border-purple-500/40',
  T5: 'bg-slate-500/20 text-slate-300 border border-slate-500/40',
}

export default function TagBadge({ tag }) {
  if (!tag) {
    return <span className="text-muted text-xs">·</span>
  }
  const style = TAG_STYLES[tag] || 'bg-slate-500/15 text-slate-300 border border-slate-500/30'
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono ${style}`}>
      {tag}
    </span>
  )
}
