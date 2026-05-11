import { useCallback, useEffect, useState } from 'react'

// Three timezones the user can rotate between. PT for west coast, EST for
// US markets, BJT for Beijing.
export const TIMEZONES = [
  { code: 'PT', label: 'PT', tz: 'America/Los_Angeles' },
  { code: 'EST', label: 'EST', tz: 'America/New_York' },
  { code: 'BJT', label: 'BJT', tz: 'Asia/Shanghai' },
]

const STORAGE_KEY = 'portfolio.timezone'

export function useTimezone() {
  const [code, setCode] = useState(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored && TIMEZONES.some((t) => t.code === stored)) return stored
    } catch (_) {}
    return 'EST'
  })

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, code)
    } catch (_) {}
  }, [code])

  const tzInfo = TIMEZONES.find((t) => t.code === code) || TIMEZONES[1]

  const formatDateTime = useCallback(
    (input, opts = {}) => {
      if (!input) return ''
      let date
      if (input instanceof Date) {
        date = input
      } else {
        let str = String(input)
        // The backend serializes naive UTC datetimes without a "Z" suffix.
        // JavaScript's Date() parses those as local time and double shifts
        // them when we apply our timezone formatter. Append "Z" if there's
        // no timezone marker present.
        if (!/[Zz]|[+-]\d{2}:?\d{2}$/.test(str)) {
          str = str + 'Z'
        }
        date = new Date(str)
      }
      if (isNaN(date.getTime())) return ''
      const merged = {
        timeZone: tzInfo.tz,
        year: 'numeric',
        month: 'short',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false,
        ...opts,
      }
      return new Intl.DateTimeFormat('en-US', merged).format(date)
    },
    [tzInfo],
  )

  const formatTime = useCallback(
    (input) =>
      formatDateTime(input, {
        year: undefined,
        month: undefined,
        day: undefined,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      }),
    [formatDateTime],
  )

  const formatDate = useCallback(
    (input) =>
      formatDateTime(input, {
        hour: undefined,
        minute: undefined,
        second: undefined,
      }),
    [formatDateTime],
  )

  return { code, setCode, tzInfo, formatDateTime, formatTime, formatDate }
}
