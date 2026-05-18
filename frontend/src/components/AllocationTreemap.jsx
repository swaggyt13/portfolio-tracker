// Treemap of current positions. Box area = market value share. Box color =
// today's percent change (green up, red down). Click a box to open it in
// TradingView. Uses d3-hierarchy for the squarified layout.

import { useEffect, useRef, useState } from 'react'
import { hierarchy, treemap } from 'd3-hierarchy'
import { openTradingView } from '../utils/tradingview.js'

function colorFor(pct) {
  if (pct == null || isNaN(Number(pct))) {
    return { bg: 'rgba(100, 116, 139, 0.18)', text: '#cbd5e1' }
  }
  const n = Number(pct)
  // Saturation scales with |change|; 5% is fully saturated.
  const intensity = Math.min(Math.abs(n) / 5, 1)
  const alpha = 0.18 + intensity * 0.55
  if (n >= 0) {
    return { bg: `rgba(34, 197, 94, ${alpha})`, text: '#86efac' }
  }
  return { bg: `rgba(239, 68, 68, ${alpha})`, text: '#fca5a5' }
}

function fmtPct(pct) {
  if (pct == null) return '·'
  const n = Number(pct)
  const sign = n >= 0 ? '+' : ''
  return `${sign}${n.toFixed(2)}%`
}

export default function AllocationTreemap({ positions }) {
  const containerRef = useRef(null)
  const [size, setSize] = useState({ width: 900, height: 540 })

  useEffect(() => {
    if (!containerRef.current) return
    const ro = new ResizeObserver((entries) => {
      const e = entries[0]
      const width = Math.max(200, Math.floor(e.contentRect.width))
      // Maintain a roughly 16:10 aspect ratio, clamp to a sensible range.
      const height = Math.max(360, Math.min(720, Math.floor(width * 0.58)))
      setSize({ width, height })
    })
    ro.observe(containerRef.current)
    return () => ro.disconnect()
  }, [])

  const items = (positions || [])
    .filter((p) => p.market_value != null && Number(p.market_value) > 0)
    .map((p) => ({
      symbol: p.symbol,
      company: p.company_name || '',
      value: Number(p.market_value),
      pct: p.day_change_pct,
      exchange: p.exchange,
      exchange_override: p.exchange_override,
    }))

  const total = items.reduce((s, d) => s + d.value, 0)

  const root = hierarchy({ children: items })
    .sum((d) => d.value || 0)
    .sort((a, b) => b.value - a.value)

  treemap()
    .size([size.width, size.height])
    .paddingInner(2)
    .paddingOuter(0)
    .round(true)(root)

  const leaves = root.leaves()

  return (
    <div ref={containerRef} className="bg-bg-panel border border-line rounded-lg p-3">
      <div className="flex items-center justify-between mb-2 px-1">
        <div className="text-xs text-muted">
          Box size = position weight · Color = today's change · Click to open in TradingView
        </div>
        <div className="text-xs text-muted font-mono">
          {items.length} positions · ${Math.round(total).toLocaleString('en-US')} total
        </div>
      </div>
      {items.length === 0 ? (
        <div className="p-8 text-center text-muted">No positions to display.</div>
      ) : (
        <svg width={size.width} height={size.height}>
          {leaves.map((leaf) => {
            const w = leaf.x1 - leaf.x0
            const h = leaf.y1 - leaf.y0
            const d = leaf.data
            const color = colorFor(d.pct)
            const weight = total > 0 ? (d.value / total) * 100 : 0
            const tiny = w < 50 || h < 36
            const small = (w < 80 || h < 60) && !tiny

            return (
              <g
                key={d.symbol}
                transform={`translate(${leaf.x0},${leaf.y0})`}
                style={{ cursor: 'pointer' }}
                onClick={() => openTradingView(d.symbol, d.exchange, d.exchange_override)}
              >
                <title>
                  {d.symbol} {d.company}
                  {'\n'}weight {weight.toFixed(1)}% · 1D {fmtPct(d.pct)}
                </title>
                <rect
                  width={w}
                  height={h}
                  fill={color.bg}
                  stroke="rgba(255,255,255,0.08)"
                  rx={4}
                />
                {tiny ? (
                  <text
                    x={w / 2}
                    y={h / 2 + 3}
                    textAnchor="middle"
                    fontSize="10"
                    fill="#f1f5f9"
                    style={{ fontFamily: 'JetBrains Mono, ui-monospace, SFMono-Regular' }}
                  >
                    {d.symbol}
                  </text>
                ) : small ? (
                  <>
                    <text
                      x={w / 2}
                      y={h / 2 - 2}
                      textAnchor="middle"
                      fontSize="12"
                      fontWeight="600"
                      fill="#f1f5f9"
                      style={{ fontFamily: 'JetBrains Mono, ui-monospace, SFMono-Regular' }}
                    >
                      {d.symbol}
                    </text>
                    <text
                      x={w / 2}
                      y={h / 2 + 12}
                      textAnchor="middle"
                      fontSize="10"
                      fill={color.text}
                      style={{ fontFamily: 'JetBrains Mono, ui-monospace, SFMono-Regular' }}
                    >
                      {fmtPct(d.pct)}
                    </text>
                  </>
                ) : (
                  <>
                    <text
                      x={w / 2}
                      y={h / 2 - 8}
                      textAnchor="middle"
                      fontSize="16"
                      fontWeight="600"
                      fill="#f1f5f9"
                      style={{ fontFamily: 'JetBrains Mono, ui-monospace, SFMono-Regular' }}
                    >
                      {d.symbol}
                    </text>
                    <text
                      x={w / 2}
                      y={h / 2 + 10}
                      textAnchor="middle"
                      fontSize="12"
                      fill={color.text}
                      style={{ fontFamily: 'JetBrains Mono, ui-monospace, SFMono-Regular' }}
                    >
                      {fmtPct(d.pct)}
                    </text>
                    <text
                      x={w / 2}
                      y={h / 2 + 26}
                      textAnchor="middle"
                      fontSize="10"
                      fill="#94a3b8"
                      style={{ fontFamily: 'JetBrains Mono, ui-monospace, SFMono-Regular' }}
                    >
                      {weight.toFixed(1)}% of book
                    </text>
                  </>
                )}
              </g>
            )
          })}
        </svg>
      )}
    </div>
  )
}
