// Simple horizontal tab strip used at the top of the dashboard.

export default function TabBar({ tabs, current, onChange }) {
  return (
    <div className="border-b border-line flex gap-1 mt-4">
      {tabs.map((t) => (
        <button
          key={t.key}
          onClick={() => onChange(t.key)}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition -mb-px ${
            current === t.key
              ? 'border-accent-blue text-slate-100'
              : 'border-transparent text-muted hover:text-slate-100'
          }`}
        >
          {t.label}
        </button>
      ))}
    </div>
  )
}
