import type { GameState, StatsState, SettingsState } from '~/types'

const defaultStats = (): StatsState => ({
  played: 0,
  wins: 0,
  currentStreak: 0,
  maxStreak: 0,
  guessDistribution: { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0 },
})

const defaultSettings = (): SettingsState => {
  if (import.meta.client) {
    const lang = navigator.language || ''
    const unit = lang.startsWith('en-US') ? 'lbs' : 'kg'
    return { unit }
  }
  return { unit: 'kg' }
}

const defaultGameState = (): GameState => ({
  guesses: [null, null, null, null, null, null],
  guessResults: [null, null, null, null, null, null],
  cluesRevealed: 0,
  solved: false,
  failed: false,
})

const todayKey = () => {
  const d = new Date()
  return `grille_state_${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, '0')}-${String(d.getUTCDate()).padStart(2, '0')}`
}

export const useStorage = () => {
  const loadGameState = (): GameState => {
    if (!import.meta.client) return defaultGameState()
    try {
      const raw = localStorage.getItem(todayKey())
      if (raw) return JSON.parse(raw) as GameState
    } catch {}
    return defaultGameState()
  }

  const saveGameState = (state: GameState) => {
    if (!import.meta.client) return
    localStorage.setItem(todayKey(), JSON.stringify(state))
  }

  const loadStats = (): StatsState => {
    if (!import.meta.client) return defaultStats()
    try {
      const raw = localStorage.getItem('grille_stats')
      if (raw) return JSON.parse(raw) as StatsState
    } catch {}
    return defaultStats()
  }

  const saveStats = (stats: StatsState) => {
    if (!import.meta.client) return
    localStorage.setItem('grille_stats', JSON.stringify(stats))
  }

  const loadSettings = (): SettingsState => {
    if (!import.meta.client) return defaultSettings()
    try {
      const raw = localStorage.getItem('grille_settings')
      if (raw) return JSON.parse(raw) as SettingsState
    } catch {}
    return defaultSettings()
  }

  const saveSettings = (settings: SettingsState) => {
    if (!import.meta.client) return
    localStorage.setItem('grille_settings', JSON.stringify(settings))
  }

  return { loadGameState, saveGameState, loadStats, saveStats, loadSettings, saveSettings }
}
