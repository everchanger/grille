import { describe, it, expect, beforeEach, vi } from 'vitest'

// Mock localStorage
const mockStore: Record<string, string> = {}
vi.stubGlobal('localStorage', {
  getItem: (key: string) => mockStore[key] ?? null,
  setItem: (key: string, val: string) => { mockStore[key] = val },
  removeItem: (key: string) => { delete mockStore[key] },
  clear: () => { Object.keys(mockStore).forEach(k => delete mockStore[k]) },
})

describe('useUnits', () => {
  beforeEach(() => {
    Object.keys(mockStore).forEach(k => delete mockStore[k])
    vi.resetModules()
  })

  it('formatWeight formats weight in kg', async () => {
    mockStore['grille_settings'] = JSON.stringify({ unit: 'kg' })
    const mod = await import('~/composables/useUnits')
    const { formatWeight } = mod.useUnits()
    expect(formatWeight(1560)).toContain('kg')
    expect(formatWeight(1560)).toContain('1,560')
  })

  it('formatWeight converts and formats weight in lbs', async () => {
    mockStore['grille_settings'] = JSON.stringify({ unit: 'lbs' })
    const mod = await import('~/composables/useUnits')
    const { formatWeight } = mod.useUnits()
    const result = formatWeight(1560)
    expect(result).toContain('lbs')
    // 1560 * 2.205 ≈ 3440
    expect(result).toContain('3,440')
  })

  it('toggleUnit switches between kg and lbs', async () => {
    mockStore['grille_settings'] = JSON.stringify({ unit: 'kg' })
    const mod = await import('~/composables/useUnits')
    const { unit, toggleUnit } = mod.useUnits()
    expect(unit.value).toBe('kg')
    toggleUnit()
    expect(unit.value).toBe('lbs')
    toggleUnit()
    expect(unit.value).toBe('kg')
  })
})
