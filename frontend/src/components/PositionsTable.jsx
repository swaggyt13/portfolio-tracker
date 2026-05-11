import { ExternalLink, Pencil, LineChart } from 'lucide-react'
import TagBadge from './TagBadge.jsx'
import EarningsBadge from './EarningsBadge.jsx'
import { fmtMoney, fmtMoneyCompact, fmtPct, pnlClass } from '../utils/format.js'
import { openTradingView, tradingViewUrl } from '../utils/tradingview.js'

function HeaderCell({ children, align = 'left' }) {
  return (
    <th
      className={`px-3 py-2 text-${align} text-[11px] font-medium text-muted uppercase tracking-wider whitespace-nowrap`}
    >
      {children}
    </th>
  )
}

function Row({ row, selected, onSelect, onEdit }) {
  const isSelected = selected === row.symbol
  const gainNum = row.pnl_percent != null ? Number(row.pnl_percent) : null
  const gainBox =
    gainNum == null
      ? <span className="text-muted">·</span>
      : (
          <span
            className={`inline-block px-1.5 py-0.5 rounded text-xs font-mono ${
              gainNum >= 0
                ? 'bg-emerald-500/20 text-emerald-300'
                : 'bg-red-500/20 text-red-300'
            }`}
          >
            {fmtPct(gainNum)}
          </span>
        )

  const dayPctNum = row.day_change_pct != null ? Number(row.day_change_pct) : null
  const dayBox =
    dayPctNum == null
      ? <span className="text-muted">·</span>
      : (
          <span
            className={`inline-block px-1.5 py-0.5 rounded text-xs font-mono ${
              dayPctNum >= 0
                ? 'bg-emerald-500/20 text-emerald-300'
                : 'bg-red-500/20 text-red-300'
            }`}
            title={
              row.day_change_dollar != null
                ? `${dayPctNum >= 0 ? '+' : ''}${Number(row.day_change_dollar).toFixed(2)} today`
                : ''
            }
          >
            {fmtPct(dayPctNum, 2)}
          </span>
        )

  // Sub line under ticker. Prefer company name; fall back to sector or exchange.
  const subline = row.company_name || row.sector || row.exchange_override || row.exchange || ''

  return (
    <tr
      onClick={() => onSelect(row.symbol)}
      onAuxClick={(e) => {
        if (e.button === 1) {
          openTradingView(row.symbol, row.exchange, row.exchange_override)
        }
      }}
      className={`border-b border-line/40 hover:bg-bg-rowHover cursor-pointer transition ${
        isSelected ? 'row-selected bg-bg-rowHover' : ''
      }`}
    >
      <td className="px-3 py-2.5 max-w-[260px]">
        <div className="font-mono font-medium text-base">{row.symbol}</div>
        <div className="text-[11px] text-muted mt-0.5 truncate" title={subline}>
          {subline}
        </div>
        {row.company_name && row.sector && (
          <div className="text-[10px] text-muted/70 truncate" title={row.sector}>
            {row.sector}
          </div>
        )}
      </td>
      <td className="px-3 py-2.5">
        <TagBadge tag={row.tag} />
      </td>
      <td className="px-3 py-2.5 text-right font-mono">{fmtMoneyCompact(row.market_value)}</td>
      <td className="px-3 py-2.5 text-right font-mono text-slate-300">{fmtMoney(row.avg_price)}</td>
      <td className="px-3 py-2.5 text-right font-mono">{fmtMoney(row.market_price)}</td>
      <td className="px-3 py-2.5 text-right">{gainBox}</td>
      <td className="px-3 py-2.5 text-right">{dayBox}</td>
      <td className={`px-3 py-2.5 text-right font-mono ${pnlClass(row.unrealized_pnl)}`}>
        {fmtMoney(row.unrealized_pnl)}
      </td>
      <td className="px-3 py-2.5">
        <EarningsBadge dateStr={row.next_earnings_date} reported={row.earnings_reported} />
      </td>
      <td className="px-3 py-2.5 text-xs font-mono text-slate-300">{row.eps_guidance || '·'}</td>
      <td className="px-3 py-2.5 text-right">
        <div className="inline-flex items-center gap-1">
          <a
            href={tradingViewUrl(row.symbol, row.exchange, row.exchange_override)}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="inline-flex items-center justify-center w-6 h-6 rounded text-muted hover:text-accent-blue hover:bg-bg-rowHover"
            title="Open in TradingView"
          >
            <LineChart size={14} />
          </a>
          <button
            onClick={(e) => {
              e.stopPropagation()
              onEdit(row)
            }}
            className="inline-flex items-center justify-center w-6 h-6 rounded text-muted hover:text-accent-blue hover:bg-bg-rowHover"
            title="Edit"
          >
            <Pencil size={14} />
          </button>
        </div>
      </td>
    </tr>
  )
}

export default function PositionsTable({ positions, selected, onSelect, onEdit }) {
  if (!positions || positions.length === 0) {
    return (
      <div className="bg-bg-panel border border-line rounded-lg p-8 text-center text-muted">
        No positions yet. Run a sync once IBKR is connected.
      </div>
    )
  }

  const openAll = () => {
    positions.forEach((row) => openTradingView(row.symbol, row.exchange, row.exchange_override))
  }

  return (
    <div>
      <div className="flex items-center justify-end pb-2">
        <button
          onClick={openAll}
          className="text-xs text-muted hover:text-accent-blue inline-flex items-center gap-1"
        >
          <ExternalLink size={12} />
          Open all in TradingView
        </button>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full">
          <thead>
            <tr className="border-b border-line">
              <HeaderCell>Ticker / Company</HeaderCell>
              <HeaderCell>Tier</HeaderCell>
              <HeaderCell align="right">Mkt Value</HeaderCell>
              <HeaderCell align="right">Avg Cost</HeaderCell>
              <HeaderCell align="right">Current</HeaderCell>
              <HeaderCell align="right">Gain</HeaderCell>
              <HeaderCell align="right">1D</HeaderCell>
              <HeaderCell align="right">Unrealized</HeaderCell>
              <HeaderCell>Next ER</HeaderCell>
              <HeaderCell>EPS Growth</HeaderCell>
              <HeaderCell align="right"></HeaderCell>
            </tr>
          </thead>
          <tbody>
            {positions.map((row) => (
              <Row
                key={`${row.account_id}_${row.symbol}`}
                row={row}
                selected={selected}
                onSelect={onSelect}
                onEdit={onEdit}
              />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
