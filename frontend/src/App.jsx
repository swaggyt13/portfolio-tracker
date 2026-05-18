import { useState } from 'react'
import Header from './components/Header.jsx'
import Legend from './components/Legend.jsx'
import TabBar from './components/TabBar.jsx'
import PositionsTable from './components/PositionsTable.jsx'
import AllocationTreemap from './components/AllocationTreemap.jsx'
import BottomSummary from './components/BottomSummary.jsx'
import MetadataModal from './components/MetadataModal.jsx'
import { usePositions } from './hooks/usePositions.js'
import { useTimezone } from './hooks/useTimezone.js'

const TABS = [
  { key: 'positions', label: 'Positions' },
  { key: 'allocation', label: 'Allocation' },
]

export default function App() {
  const { positions, summary, loading, error, syncing, forceSync, updateMetadata } = usePositions()
  const { code, setCode, formatDate, formatTime } = useTimezone()
  const [selected, setSelected] = useState(null)
  const [editing, setEditing] = useState(null)
  const [tab, setTab] = useState('positions')

  return (
    <div className="min-h-screen flex flex-col">
      <main className="flex-1 max-w-[1500px] w-full mx-auto px-6 py-6">
        <Header
          count={positions.length}
          lastSyncedAt={summary?.last_synced_at}
          tzCode={code}
          setTzCode={setCode}
          formatDate={formatDate}
          formatTime={formatTime}
        />
        <Legend />
        <TabBar tabs={TABS} current={tab} onChange={setTab} />

        {error && (
          <div className="mt-4 bg-accent-red/10 border border-accent-red/40 text-accent-red rounded px-4 py-2 text-sm">
            {error}
          </div>
        )}

        <div className="mt-4">
          {loading ? (
            <div className="bg-bg-panel border border-line rounded-lg p-8 text-center text-muted">
              Loading positions...
            </div>
          ) : tab === 'positions' ? (
            <PositionsTable
              positions={positions}
              selected={selected}
              onSelect={setSelected}
              onEdit={setEditing}
            />
          ) : (
            <AllocationTreemap positions={positions} />
          )}
        </div>

        <BottomSummary
          summary={summary}
          positions={positions}
          syncing={syncing}
          onSync={forceSync}
        />
      </main>

      <footer className="border-t border-line text-xs text-muted">
        <div className="max-w-[1500px] mx-auto px-6 py-3 flex items-center justify-between">
          <span>Click a row to select. Click the chart icon or middle click to open TradingView.</span>
          <span className="font-mono">{positions.length} positions</span>
        </div>
      </footer>

      {editing && (
        <MetadataModal
          row={editing}
          onClose={() => setEditing(null)}
          onSave={updateMetadata}
        />
      )}
    </div>
  )
}
