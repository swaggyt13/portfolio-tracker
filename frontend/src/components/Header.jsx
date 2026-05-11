import TimezonePicker from './TimezonePicker.jsx'

export default function Header({ count, lastSyncedAt, tzCode, setTzCode, formatDate, formatTime }) {
  const now = new Date()
  return (
    <div className="flex items-start justify-between pb-4 border-b border-line">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Portfolio Tracker</h1>
        <div className="text-xs text-muted mt-1">Holdings sorted by gain</div>
      </div>
      <div className="text-right">
        <div className="text-xs text-muted font-mono">{formatDate(now)} · intraday</div>
        <div className="text-xs text-muted font-mono mt-0.5">{count} holdings</div>
        <div className="mt-2 flex items-center justify-end gap-2">
          <span className="text-[10px] text-muted">
            {lastSyncedAt ? `last sync ${formatTime(lastSyncedAt)}` : 'awaiting sync'}
          </span>
          <TimezonePicker code={tzCode} onChange={setTzCode} />
        </div>
      </div>
    </div>
  )
}
