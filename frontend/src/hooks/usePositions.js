import { useCallback, useEffect, useState } from 'react'
import { api } from '../utils/api.js'

const POLL_MS = 30000

export function usePositions() {
  const [positions, setPositions] = useState([])
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [syncing, setSyncing] = useState(false)

  const refresh = useCallback(async () => {
    try {
      const [pos, sum] = await Promise.all([api.positions(), api.summary()])
      setPositions(pos)
      setSummary(sum)
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  const forceSync = useCallback(async () => {
    setSyncing(true)
    try {
      await api.forceSync()
      await refresh()
    } catch (err) {
      setError(err.message)
    } finally {
      setSyncing(false)
    }
  }, [refresh])

  const updateMetadata = useCallback(
    async (symbol, payload) => {
      await api.updateMetadata(symbol, payload)
      await refresh()
    },
    [refresh],
  )

  useEffect(() => {
    refresh()
    const id = setInterval(refresh, POLL_MS)
    return () => clearInterval(id)
  }, [refresh])

  return { positions, summary, loading, error, syncing, refresh, forceSync, updateMetadata }
}
