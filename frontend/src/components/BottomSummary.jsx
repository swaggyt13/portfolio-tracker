// Bottom strip with average gain, top performer, win count, and a 14 day
// earnings list.

import { earningsUrgency, fmtPct, pnlClass } from '../utils/format.js'

function urgencyDot(level) {
  const map = {
    red: 'bg-red-500',
    orange: 'bg-orange-500',
    yellow: 'bg-yellow-400',
  }
  return map[level] || 'bg-slate-400'
}

export default function BottomSummary({ summary, positions, syncing, onSync }) {
  if (!summary) return null

  const upcoming = (positions || [])
    .map((p) => ({ ...p, _level: earningsUrgency(p.next_earnings_date, p.earnings_reported) }))
    .filter((p) => p._level)
    .sort((a, b) => (a.next_earnings_date || '').localeCompare(b.next_earnings_date || ''))

  return (
    <div className="border-t border-line pt-4 mt-6 grid grid-cols-1 md:grid-cols-4 gap-6">
      <div>
        <div className="text-xs text-muted">Average Gain</div>
        <div className={`mt-1 text-2xl font-mono ${pnlClass(summary.total_return_pct)}`}>
          {fmtPct(summary.total_return_pct, 1)}
        </div>
      </div>

      <div>
        <div className="text-xs text-muted">Top Performer</div>
        <div className="mt-1 text-2xl font-mono">
          {summary.top_performer_symbol ? (
            <>
              <span className="text-slate-100">{summary.top_performer_symbol}</span>
              <span className="text-accent-green ml-2">{fmtPct(summary.top_performer_pnl_pct)}</span>
            </>
          ) : (
            <span className="text-muted">·</span>
          )}
        </div>
      </div>

      <div>
        <div className="text-xs text-muted">Winners</div>
        <div className="mt-1 text-2xl font-mono">
          {summary.win_count} / {summary.position_count}
        </div>
      </div>

      <div>
        <div className="flex items-center justify-between">
          <div className="text-xs text-muted">Earnings within 14 days ({upcoming.length})</div>
          <button
            onClick={onSync}
            disabled={syncing}
            className="text-[11px] text-muted hover:text-accent-blue disabled:opacity-50"
          >
            {syncing ? 'syncing...' : 'force sync'}
          </button>
        </div>
        <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1">
          {upcoming.length === 0 ? (
            <span className="text-muted text-xs">·</span>
          ) : (
            upcoming.map((p) => (
              <span key={p.symbol} className="inline-flex items-center gap-1 text-xs font-mono">
                <span className={`w-1.5 h-1.5 rounded-full ${urgencyDot(p._level)}`} />
                {p.symbol}
              </span>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
