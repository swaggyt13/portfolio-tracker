import { useEffect, useState } from 'react'
import { X } from 'lucide-react'

const TAGS = ['', 'T1', 'T2', 'T3', 'T4']

export default function MetadataModal({ row, onClose, onSave }) {
  const [tag, setTag] = useState(row?.tag || '')
  const [sector, setSector] = useState(row?.sector || '')
  const [eps, setEps] = useState(row?.eps_guidance || '')
  const [notes, setNotes] = useState(row?.notes || '')
  const [earnings, setEarnings] = useState(row?.next_earnings_date || '')
  const [reported, setReported] = useState(!!row?.earnings_reported)
  const [exchange, setExchange] = useState(row?.exchange_override || '')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    setTag(row?.tag || '')
    setSector(row?.sector || '')
    setEps(row?.eps_guidance || '')
    setNotes(row?.notes || '')
    setEarnings(row?.next_earnings_date || '')
    setReported(!!row?.earnings_reported)
    setExchange(row?.exchange_override || '')
  }, [row])

  if (!row) return null

  const submit = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      await onSave(row.symbol, {
        tag: tag || null,
        sector,
        eps_guidance: eps,
        notes,
        next_earnings_date: earnings || null,
        earnings_reported: reported,
        exchange_override: exchange || null,
      })
      onClose()
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <form
        onSubmit={submit}
        className="bg-bg-panel border border-line rounded-lg w-full max-w-md p-5 space-y-4"
      >
        <div className="flex items-center justify-between">
          <h3 className="font-mono font-semibold">{row.symbol}</h3>
          <button type="button" onClick={onClose} className="text-muted hover:text-slate-100">
            <X size={16} />
          </button>
        </div>

        <div>
          <label className="block text-xs text-muted mb-1">Tier</label>
          <div className="flex gap-2">
            {TAGS.map((t) => (
              <button
                key={t || 'none'}
                type="button"
                onClick={() => setTag(t)}
                className={`px-3 py-1 rounded text-xs font-mono border ${
                  tag === t
                    ? 'border-accent-blue bg-accent-blue/15 text-accent-blue'
                    : 'border-line text-muted hover:text-slate-100'
                }`}
              >
                {t || 'none'}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-xs text-muted mb-1">Sector</label>
          <input
            type="text"
            placeholder="Semi Equipment, Optics, ..."
            value={sector}
            onChange={(e) => setSector(e.target.value)}
            className="w-full bg-bg border border-line rounded px-3 py-2 text-sm focus:outline-none focus:border-accent-blue"
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs text-muted mb-1">Next Earnings</label>
            <input
              type="date"
              value={earnings}
              onChange={(e) => setEarnings(e.target.value)}
              className="w-full bg-bg border border-line rounded px-3 py-2 text-sm font-mono focus:outline-none focus:border-accent-blue"
            />
          </div>
          <div>
            <label className="block text-xs text-muted mb-1">EPS Guidance</label>
            <input
              type="text"
              placeholder="+18~22%, TBD, Improving"
              value={eps}
              onChange={(e) => setEps(e.target.value)}
              className="w-full bg-bg border border-line rounded px-3 py-2 text-sm focus:outline-none focus:border-accent-blue"
            />
          </div>
        </div>

        <div className="flex items-center gap-2">
          <input
            id="reported"
            type="checkbox"
            checked={reported}
            onChange={(e) => setReported(e.target.checked)}
            className="accent-accent-blue"
          />
          <label htmlFor="reported" className="text-xs text-muted">
            Already reported this quarter
          </label>
        </div>

        <div>
          <label className="block text-xs text-muted mb-1">Exchange Override</label>
          <input
            type="text"
            placeholder="NASDAQ, NYSE, ..."
            value={exchange}
            onChange={(e) => setExchange(e.target.value.toUpperCase())}
            className="w-full bg-bg border border-line rounded px-3 py-2 text-sm font-mono focus:outline-none focus:border-accent-blue"
          />
        </div>

        <div>
          <label className="block text-xs text-muted mb-1">Notes</label>
          <textarea
            rows={3}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="w-full bg-bg border border-line rounded px-3 py-2 text-sm focus:outline-none focus:border-accent-blue"
          />
        </div>

        <div className="flex justify-end gap-2 pt-2">
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-1.5 text-sm text-muted hover:text-slate-100"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={saving}
            className="px-3 py-1.5 text-sm bg-accent-blue text-white rounded hover:bg-blue-500 disabled:opacity-50"
          >
            {saving ? 'Saving' : 'Save'}
          </button>
        </div>
      </form>
    </div>
  )
}
