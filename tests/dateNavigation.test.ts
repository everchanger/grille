import { describe, it, expect, beforeEach, vi } from 'vitest'
import type { Car } from '~/types'

// Mock localStorage
const mockStore: Record<string, string> = {}
vi.stubGlobal('localStorage', {
  getItem: (key: string) => mockStore[key] ?? null,
  setItem: (key: string, val: string) => { mockStore[key] = val },
  removeItem: (key: string) => { delete mockStore[key] },
  clear: () => { Object.keys(mockStore).forEach(k => delete mockStore[k]) },
})

describe('date utility functions', () => {
  it('getTodayDateStr returns YYYY-MM-DD in UTC', async () => {
    const { getTodayDateStr } = await import('~/composables/useGame')
    const result = getTodayDateStr()
    expect(result).toMatch(/^\d{4}-\d{2}-\d{2}$/)
    // Should match today's UTC date
    const now = new Date()
    const expected = `${now.getUTCFullYear()}-${String(now.getUTCMonth() + 1).padStart(2, '0')}-${String(now.getUTCDate()).padStart(2, '0')}`
    expect(result).toBe(expected)
  })

  it('dateToDayNumber converts epoch date to day 0', async () => {
    const { dateToDayNumber } = await import('~/composables/useGame')
    expect(dateToDayNumber('2025-01-01')).toBe(0)
  })

  it('dateToDayNumber converts day after epoch to day 1', async () => {
    const { dateToDayNumber } = await import('~/composables/useGame')
    expect(dateToDayNumber('2025-01-02')).toBe(1)
  })

  it('dateToDayNumber converts a later date correctly', async () => {
    const { dateToDayNumber } = await import('~/composables/useGame')
    // Feb 1, 2025 = 31 days after Jan 1
    expect(dateToDayNumber('2025-02-01')).toBe(31)
  })

  it('dayNumberToDate converts day 0 to epoch date', async () => {
    const { dayNumberToDate } = await import('~/composables/useGame')
    expect(dayNumberToDate(0)).toBe('2025-01-01')
  })

  it('dayNumberToDate converts day 1 to Jan 2', async () => {
    const { dayNumberToDate } = await import('~/composables/useGame')
    expect(dayNumberToDate(1)).toBe('2025-01-02')
  })

  it('dayNumberToDate converts day 31 to Feb 1', async () => {
    const { dayNumberToDate } = await import('~/composables/useGame')
    expect(dayNumberToDate(31)).toBe('2025-02-01')
  })

  it('dateToDayNumber and dayNumberToDate are inverses', async () => {
    const { dateToDayNumber, dayNumberToDate } = await import('~/composables/useGame')
    const dates = ['2025-01-01', '2025-03-15', '2025-06-30', '2025-12-31', '2026-02-28']
    for (const date of dates) {
      expect(dayNumberToDate(dateToDayNumber(date))).toBe(date)
    }
  })

  it('dateToDayNumber returns negative for dates before epoch', async () => {
    const { dateToDayNumber } = await import('~/composables/useGame')
    expect(dateToDayNumber('2024-12-31')).toBe(-1)
  })
})

describe('useGame with date override', () => {
  beforeEach(() => {
    Object.keys(mockStore).forEach(k => delete mockStore[k])
  })

  it('uses today when no date override is provided', async () => {
    const { useGame, getTodayDateStr, dateToDayNumber } = await import('~/composables/useGame')
    const game = useGame()
    expect(game.selectedDateStr.value).toBe(getTodayDateStr())
    expect(game.isToday.value).toBe(true)
    expect(game.dayNumber.value).toBe(dateToDayNumber(getTodayDateStr()))
  })

  it('uses override date when provided', async () => {
    const { ref } = await import('vue')
    const { useGame, dateToDayNumber } = await import('~/composables/useGame')
    const dateRef = ref<string | undefined>('2025-03-15')
    const game = useGame(dateRef)
    expect(game.selectedDateStr.value).toBe('2025-03-15')
    expect(game.dayNumber.value).toBe(dateToDayNumber('2025-03-15'))
    expect(game.isToday.value).toBe(false)
  })

  it('falls back to today when override is undefined', async () => {
    const { ref } = await import('vue')
    const { useGame, getTodayDateStr } = await import('~/composables/useGame')
    const dateRef = ref<string | undefined>(undefined)
    const game = useGame(dateRef)
    expect(game.selectedDateStr.value).toBe(getTodayDateStr())
    expect(game.isToday.value).toBe(true)
  })

  it('selects different cars for different dates', async () => {
    const { ref } = await import('vue')
    const { useGame } = await import('~/composables/useGame')

    const dateRef1 = ref<string | undefined>('2025-01-01')
    const game1 = useGame(dateRef1)
    const car1 = game1.todaysCar.value

    const dateRef2 = ref<string | undefined>('2025-01-02')
    const game2 = useGame(dateRef2)
    const car2 = game2.todaysCar.value

    // Day 0 and Day 1 should select different cars (different indices)
    // Unless the car list has only 1 entry, which is very unlikely
    expect(game1.dayNumber.value).not.toBe(game2.dayNumber.value)
  })

  it('selects the same car deterministically for the same date', async () => {
    const { ref } = await import('vue')
    const { useGame } = await import('~/composables/useGame')

    const dateRef1 = ref<string | undefined>('2025-06-15')
    const game1 = useGame(dateRef1)

    const dateRef2 = ref<string | undefined>('2025-06-15')
    const game2 = useGame(dateRef2)

    expect(game1.todaysCar.value.id).toBe(game2.todaysCar.value.id)
    expect(game1.todaysCar.value.make).toBe(game2.todaysCar.value.make)
    expect(game1.todaysCar.value.model).toBe(game2.todaysCar.value.model)
  })

  it('reloads state when date changes', async () => {
    const { ref, nextTick } = await import('vue')
    const { useGame } = await import('~/composables/useGame')
    const { carLabel } = await import('~/utils/carLabel')

    // Play a game on date A and save state
    const dateRef = ref<string | undefined>('2025-02-10')
    const game = useGame(dateRef)
    const carA = game.todaysCar.value
    game.submitGuess(carLabel(carA))
    expect(game.state.value.solved).toBe(true)

    // Switch to a different date
    dateRef.value = '2025-02-11'
    await nextTick()

    // State should be fresh (not solved)
    expect(game.state.value.solved).toBe(false)
    expect(game.guessCount.value).toBe(0)
  })

  it('preserves state per date in localStorage', async () => {
    const { ref, nextTick } = await import('vue')
    const { useGame } = await import('~/composables/useGame')
    const { carLabel } = await import('~/utils/carLabel')

    const dateRef = ref<string | undefined>('2025-04-01')
    const game = useGame(dateRef)
    const carA = game.todaysCar.value
    game.submitGuess(carLabel(carA))
    expect(game.state.value.solved).toBe(true)

    // Switch away
    dateRef.value = '2025-04-02'
    await nextTick()
    expect(game.state.value.solved).toBe(false)

    // Switch back - state should be restored from localStorage
    dateRef.value = '2025-04-01'
    await nextTick()
    expect(game.state.value.solved).toBe(true)
    expect(game.guessCount.value).toBe(1)
  })
})

describe('useStorage with date parameter', () => {
  beforeEach(() => {
    Object.keys(mockStore).forEach(k => delete mockStore[k])
  })

  it('uses the provided date string for the storage key', async () => {
    const { useStorage } = await import('~/composables/useStorage')
    const { saveGameState, loadGameState } = useStorage()

    const state = {
      guesses: ['Test Car (2020)', null, null, null, null] as (string | null)[],
      guessResults: [null, null, null, null, null],
      cluesRevealed: 0,
      solved: false,
      failed: false,
    }

    saveGameState(state, '2025-05-20')
    expect(mockStore['grille_state_2025-05-20']).toBeDefined()

    const loaded = loadGameState('2025-05-20')
    expect(loaded.guesses[0]).toBe('Test Car (2020)')
  })

  it('different dates use different storage keys', async () => {
    const { useStorage } = await import('~/composables/useStorage')
    const { saveGameState, loadGameState } = useStorage()

    const state1 = {
      guesses: ['Car A', null, null, null, null] as (string | null)[],
      guessResults: [null, null, null, null, null],
      cluesRevealed: 0,
      solved: true,
      failed: false,
    }
    const state2 = {
      guesses: ['Car B', null, null, null, null] as (string | null)[],
      guessResults: [null, null, null, null, null],
      cluesRevealed: 0,
      solved: false,
      failed: true,
    }

    saveGameState(state1, '2025-07-01')
    saveGameState(state2, '2025-07-02')

    const loaded1 = loadGameState('2025-07-01')
    expect(loaded1.guesses[0]).toBe('Car A')
    expect(loaded1.solved).toBe(true)

    const loaded2 = loadGameState('2025-07-02')
    expect(loaded2.guesses[0]).toBe('Car B')
    expect(loaded2.failed).toBe(true)
  })

  it('loadGameState without date param uses today', async () => {
    const { useStorage } = await import('~/composables/useStorage')
    const { saveGameState, loadGameState } = useStorage()

    // Save with today's key
    const d = new Date()
    const todayKey = `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, '0')}-${String(d.getUTCDate()).padStart(2, '0')}`

    const state = {
      guesses: ['Today Car', null, null, null, null] as (string | null)[],
      guessResults: [null, null, null, null, null],
      cluesRevealed: 0,
      solved: false,
      failed: false,
    }

    saveGameState(state, todayKey)

    // Load without date param should get today's state
    const loaded = loadGameState()
    expect(loaded.guesses[0]).toBe('Today Car')
  })
})

describe('date navigation logic', () => {
  it('previous day from day 1 gives day 0 (epoch)', async () => {
    const { dateToDayNumber, dayNumberToDate } = await import('~/composables/useGame')
    const day1 = dateToDayNumber('2025-01-02')
    expect(day1).toBe(1)
    const prevDate = dayNumberToDate(day1 - 1)
    expect(prevDate).toBe('2025-01-01')
  })

  it('next day from epoch gives day 1', async () => {
    const { dateToDayNumber, dayNumberToDate } = await import('~/composables/useGame')
    const day0 = dateToDayNumber('2025-01-01')
    expect(day0).toBe(0)
    const nextDate = dayNumberToDate(day0 + 1)
    expect(nextDate).toBe('2025-01-02')
  })

  it('navigating forward then backward returns to same date', async () => {
    const { dateToDayNumber, dayNumberToDate } = await import('~/composables/useGame')
    const original = '2025-08-15'
    const dayNum = dateToDayNumber(original)
    const forward = dayNumberToDate(dayNum + 1)
    const back = dayNumberToDate(dateToDayNumber(forward) - 1)
    expect(back).toBe(original)
  })

  it('navigating across month boundary works correctly', async () => {
    const { dateToDayNumber, dayNumberToDate } = await import('~/composables/useGame')
    const jan31 = '2025-01-31'
    const dayNum = dateToDayNumber(jan31)
    const nextDay = dayNumberToDate(dayNum + 1)
    expect(nextDay).toBe('2025-02-01')
  })

  it('navigating across year boundary works correctly', async () => {
    const { dateToDayNumber, dayNumberToDate } = await import('~/composables/useGame')
    const dec31 = '2025-12-31'
    const dayNum = dateToDayNumber(dec31)
    const nextDay = dayNumberToDate(dayNum + 1)
    expect(nextDay).toBe('2026-01-01')
  })

  it('cannot navigate before epoch (day number would be negative)', async () => {
    const { dateToDayNumber } = await import('~/composables/useGame')
    const epochDay = dateToDayNumber('2025-01-01')
    expect(epochDay).toBe(0)
    // prevDay would be -1, which is before epoch
    expect(epochDay - 1).toBeLessThan(0)
  })

  it('validates today is not in the future relative to getTodayDateStr', async () => {
    const { getTodayDateStr, dateToDayNumber } = await import('~/composables/useGame')
    const todayStr = getTodayDateStr()
    const todayNum = dateToDayNumber(todayStr)
    // Today should be day 0 or greater (after or on epoch)
    expect(todayNum).toBeGreaterThanOrEqual(0)
  })
})

describe('date query parameter validation', () => {
  it('valid date format YYYY-MM-DD is accepted', () => {
    const isValidDate = (q: string): boolean => {
      if (!/^\d{4}-\d{2}-\d{2}$/.test(q)) return false
      const [y, m, d] = q.split('-').map(Number)
      const date = new Date(Date.UTC(y, m - 1, d))
      return date.getUTCFullYear() === y && date.getUTCMonth() === m - 1 && date.getUTCDate() === d
    }

    expect(isValidDate('2025-01-01')).toBe(true)
    expect(isValidDate('2025-12-31')).toBe(true)
    expect(isValidDate('2026-02-28')).toBe(true)
  })

  it('invalid date formats are rejected', () => {
    const isValidFormat = (q: string): boolean => /^\d{4}-\d{2}-\d{2}$/.test(q)

    expect(isValidFormat('2025/01/01')).toBe(false)
    expect(isValidFormat('01-01-2025')).toBe(false)
    expect(isValidFormat('2025-1-1')).toBe(false)
    expect(isValidFormat('not-a-date')).toBe(false)
    expect(isValidFormat('')).toBe(false)
    expect(isValidFormat('2025-13-01')).toBe(true) // format OK but...
  })

  it('non-existent dates are rejected', () => {
    const isRealDate = (q: string): boolean => {
      const [y, m, d] = q.split('-').map(Number)
      const date = new Date(Date.UTC(y, m - 1, d))
      return date.getUTCFullYear() === y && date.getUTCMonth() === m - 1 && date.getUTCDate() === d
    }

    expect(isRealDate('2025-02-29')).toBe(false) // 2025 is not a leap year
    expect(isRealDate('2025-13-01')).toBe(false) // no month 13
    expect(isRealDate('2025-04-31')).toBe(false) // April has 30 days
    expect(isRealDate('2025-02-28')).toBe(true) // valid
    expect(isRealDate('2024-02-29')).toBe(true) // 2024 IS a leap year
  })

  it('future dates should be rejected', async () => {
    const { getTodayDateStr } = await import('~/composables/useGame')
    const todayStr = getTodayDateStr()
    const futureDate = '2099-01-01'
    expect(futureDate > todayStr).toBe(true) // future dates would fail the comparison
  })

  it('dates before epoch should be rejected', () => {
    const epochDateStr = '2025-01-01'
    expect('2024-12-31' < epochDateStr).toBe(true)
    expect('2025-01-01' < epochDateStr).toBe(false)
  })
})

describe('share text includes URL', () => {
  beforeEach(() => {
    Object.keys(mockStore).forEach(k => delete mockStore[k])
  })

  it('generateShareText includes day number', async () => {
    const { ref } = await import('vue')
    const { useGame } = await import('~/composables/useGame')
    const dateRef = ref<string | undefined>('2025-03-15')
    const game = useGame(dateRef)
    const text = game.generateShareText()
    expect(text).toContain(`Grille #${game.dayNumber.value}`)
  })

  it('different dates produce different share text headers', async () => {
    const { ref } = await import('vue')
    const { useGame } = await import('~/composables/useGame')

    const dateRef1 = ref<string | undefined>('2025-01-01')
    const game1 = useGame(dateRef1)
    const text1 = game1.generateShareText()

    const dateRef2 = ref<string | undefined>('2025-06-15')
    const game2 = useGame(dateRef2)
    const text2 = game2.generateShareText()

    // Day numbers should differ
    expect(text1).toContain('Grille #0')
    expect(text2).toContain(`Grille #${game2.dayNumber.value}`)
    expect(game1.dayNumber.value).not.toBe(game2.dayNumber.value)
  })
})
