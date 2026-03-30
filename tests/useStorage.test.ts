import { describe, it, expect, beforeEach, vi } from 'vitest'

// Mock localStorage
const mockStore: Record<string, string> = {}
vi.stubGlobal('localStorage', {
  getItem: (key: string) => mockStore[key] ?? null,
  setItem: (key: string, val: string) => { mockStore[key] = val },
  removeItem: (key: string) => { delete mockStore[key] },
  clear: () => { Object.keys(mockStore).forEach(k => delete mockStore[k]) },
})

describe('useStorage', () => {
  beforeEach(() => {
    Object.keys(mockStore).forEach(k => delete mockStore[k])
  })

  it('loadGameState returns default state when nothing is stored', async () => {
    const { useStorage } = await import('~/composables/useStorage')
    const { loadGameState } = useStorage()
    const state = loadGameState()
    expect(state.guesses).toHaveLength(5)
    expect(state.guesses.every(g => g === null)).toBe(true)
    expect(state.guessResults).toHaveLength(5)
    expect(state.solved).toBe(false)
    expect(state.failed).toBe(false)
  })

  it('saveGameState and loadGameState round-trip correctly', async () => {
    const { useStorage } = await import('~/composables/useStorage')
    const { saveGameState, loadGameState } = useStorage()

    const state = {
      guesses: ['Toyota Supra (A80) (1993)', null, null, null, null] as (string | null)[],
      guessResults: [
        { make: 'correct' as const, model: 'correct' as const, year: 'correct' as const, horsepower: 'correct' as const, weight: 'correct' as const },
        null, null, null, null,
      ],
      cluesRevealed: 0,
      solved: true,
      failed: false,
    }
    saveGameState(state)
    const loaded = loadGameState()
    expect(loaded.guesses[0]).toBe('Toyota Supra (A80) (1993)')
    expect(loaded.solved).toBe(true)
  })

  it('loadStats returns default stats when nothing is stored', async () => {
    const { useStorage } = await import('~/composables/useStorage')
    const { loadStats } = useStorage()
    const stats = loadStats()
    expect(stats.played).toBe(0)
    expect(stats.wins).toBe(0)
    expect(stats.currentStreak).toBe(0)
    expect(stats.maxStreak).toBe(0)
  })

  it('saveStats and loadStats round-trip correctly', async () => {
    const { useStorage } = await import('~/composables/useStorage')
    const { saveStats, loadStats } = useStorage()

    const stats = {
      played: 5,
      wins: 3,
      currentStreak: 2,
      maxStreak: 3,
      guessDistribution: { 1: 1, 2: 1, 3: 1, 4: 0, 5: 0, 6: 0 },
    }
    saveStats(stats)
    const loaded = loadStats()
    expect(loaded.played).toBe(5)
    expect(loaded.wins).toBe(3)
    expect(loaded.currentStreak).toBe(2)
  })

  it('loadSettings returns default settings', async () => {
    const { useStorage } = await import('~/composables/useStorage')
    const { loadSettings } = useStorage()
    const settings = loadSettings()
    expect(settings.unit).toMatch(/^(kg|lbs)$/)
  })

  it('saveSettings and loadSettings round-trip correctly', async () => {
    const { useStorage } = await import('~/composables/useStorage')
    const { saveSettings, loadSettings } = useStorage()

    saveSettings({ unit: 'lbs' })
    const loaded = loadSettings()
    expect(loaded.unit).toBe('lbs')
  })

  it('handles corrupted localStorage data gracefully', async () => {
    mockStore['grille_stats'] = '{invalid json'
    const { useStorage } = await import('~/composables/useStorage')
    const { loadStats } = useStorage()
    const stats = loadStats()
    expect(stats.played).toBe(0)
  })
})
