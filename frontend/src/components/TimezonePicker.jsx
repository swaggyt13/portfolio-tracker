import { TIMEZONES } from '../hooks/useTimezone.js'

export default function TimezonePicker({ code, onChange }) {
  return (
    <div className="inline-flex rounded border border-line overflow-hidden text-xs font-mono">
      {TIMEZONES.map((t) => (
        <button
          key={t.code}
          onClick={() => onChange(t.code)}
          className={`px-2 py-1 transition ${
            code === t.code
              ? 'bg-accent-blue/20 text-accent-blue'
              : 'text-muted hover:text-slate-100 hover:bg-bg-rowHover'
          }`}
        >
          {t.label}
        </button>
      ))}
    </div>
  )
}
