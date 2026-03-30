import { describe, it, expect, beforeEach, vi } from 'vitest'
import type { Car, GuessFeedback } from '~/types'

// Mock localStorage
const mockStore: Record<string, string> = {}
vi.stubGlobal('localStorage', {
  getItem: (key: string) => mockStore[key] ?? null,
  setItem: (key: string, val: string) => { mockStore[key] = val },
  removeItem: (key: string) => { delete mockStore[key] },
  clear: () => { Object.keys(mockStore).forEach(k => delete mockStore[k]) },
})

const makeCar = (overrides: Partial<Car> = {}): Car => ({
  id: 1,
  make: 'Toyota',
  model: 'Supra (A80)',
  year: 1993,
  country: 'Japan',
  horsepower: 320,
  weight_kg: 1560,
  engine: 'I6 Twin Turbo',
  drivetrain: 'RWD',
  image: '/cars/toyota-supra-a80.webp',
  fact: 'A great car.',
  wiki: 'https://en.wikipedia.org/wiki/Toyota_Supra',
  ...overrides,
})

describe('useGame', () => {
  beforeEach(() => {
    Object.keys(mockStore).forEach(k => delete mockStore[k])
  })

  describe('computeFeedback', () => {
    // Import useGame dynamically to get fresh instances
    const getComputeFeedback = async () => {
      const { useGame } = await import('~/composables/useGame')
      return useGame().computeFeedback
    }

    it('returns all correct when cars match exactly', async () => {
      const computeFeedback = await getComputeFeedback()
      const car = makeCar()
      const feedback = computeFeedback(car, car)
      expect(feedback).toEqual({
        make: 'correct',
        model: 'correct',
        year: 'correct',
        country: 'correct',
        horsepower: 'correct',
        weight: 'correct',
      })
    })

    it('returns wrong for different make and model', async () => {
      const computeFeedback = await getComputeFeedback()
      const guessed = makeCar({ make: 'Mazda', model: 'RX-7 (FD)' })
      const answer = makeCar({ make: 'Toyota', model: 'Supra (A80)' })
      const feedback = computeFeedback(guessed, answer)
      expect(feedback.make).toBe('wrong')
      expect(feedback.model).toBe('wrong')
    })

    it('returns wrong for different country', async () => {
      const computeFeedback = await getComputeFeedback()
      const guessed = makeCar({ country: 'USA' })
      const answer = makeCar({ country: 'Japan' })
      const feedback = computeFeedback(guessed, answer)
      expect(feedback.country).toBe('wrong')
    })

    it('returns higher when guessed year is less than answer year', async () => {
      const computeFeedback = await getComputeFeedback()
      const guessed = makeCar({ year: 1990 })
      const answer = makeCar({ year: 1995 })
      const feedback = computeFeedback(guessed, answer)
      expect(feedback.year).toBe('higher')
    })

    it('returns lower when guessed year is greater than answer year', async () => {
      const computeFeedback = await getComputeFeedback()
      const guessed = makeCar({ year: 1999 })
      const answer = makeCar({ year: 1992 })
      const feedback = computeFeedback(guessed, answer)
      expect(feedback.year).toBe('lower')
    })

    it('returns close_higher when HP difference is within 15% and guessed is lower', async () => {
      const computeFeedback = await getComputeFeedback()
      const guessed = makeCar({ horsepower: 280 })
      const answer = makeCar({ horsepower: 320 })
      // diff = |280-320|/320 = 40/320 = 0.125 <= 0.15 → close_higher
      const feedback = computeFeedback(guessed, answer)
      expect(feedback.horsepower).toBe('close_higher')
    })

    it('returns close_lower when HP difference is within 15% and guessed is higher', async () => {
      const computeFeedback = await getComputeFeedback()
      const guessed = makeCar({ horsepower: 350 })
      const answer = makeCar({ horsepower: 320 })
      // diff = |350-320|/320 = 30/320 = 0.09375 <= 0.15 → close_lower
      const feedback = computeFeedback(guessed, answer)
      expect(feedback.horsepower).toBe('close_lower')
    })

    it('returns higher when HP is much lower than answer', async () => {
      const computeFeedback = await getComputeFeedback()
      const guessed = makeCar({ horsepower: 118 })
      const answer = makeCar({ horsepower: 320 })
      const feedback = computeFeedback(guessed, answer)
      expect(feedback.horsepower).toBe('higher')
    })

    it('returns lower when HP is much higher than answer', async () => {
      const computeFeedback = await getComputeFeedback()
      const guessed = makeCar({ horsepower: 400 })
      const answer = makeCar({ horsepower: 200 })
      const feedback = computeFeedback(guessed, answer)
      expect(feedback.horsepower).toBe('lower')
    })

    it('returns close_higher when weight difference is within 10% and guessed is lower', async () => {
      const computeFeedback = await getComputeFeedback()
      const guessed = makeCar({ weight_kg: 1450 })
      const answer = makeCar({ weight_kg: 1560 })
      // diff = |1450-1560|/1560 = 110/1560 ≈ 0.0705 <= 0.1 → close_higher
      const feedback = computeFeedback(guessed, answer)
      expect(feedback.weight).toBe('close_higher')
    })

    it('returns close_lower when weight difference is within 10% and guessed is higher', async () => {
      const computeFeedback = await getComputeFeedback()
      const guessed = makeCar({ weight_kg: 1650 })
      const answer = makeCar({ weight_kg: 1560 })
      // diff = |1650-1560|/1560 = 90/1560 ≈ 0.0577 <= 0.1 → close_lower
      const feedback = computeFeedback(guessed, answer)
      expect(feedback.weight).toBe('close_lower')
    })

    it('returns higher when weight is much lower than answer', async () => {
      const computeFeedback = await getComputeFeedback()
      const guessed = makeCar({ weight_kg: 725 })
      const answer = makeCar({ weight_kg: 1560 })
      const feedback = computeFeedback(guessed, answer)
      expect(feedback.weight).toBe('higher')
    })

    it('returns lower when weight is much higher than answer', async () => {
      const computeFeedback = await getComputeFeedback()
      const guessed = makeCar({ weight_kg: 1560 })
      const answer = makeCar({ weight_kg: 725 })
      const feedback = computeFeedback(guessed, answer)
      expect(feedback.weight).toBe('lower')
    })
  })

  describe('game flow', () => {
    it('loads with default state', async () => {
      const { useGame } = await import('~/composables/useGame')
      const game = useGame()
      expect(game.guessCount.value).toBe(0)
      expect(game.canGuess.value).toBe(true)
      expect(game.state.value.solved).toBe(false)
      expect(game.state.value.failed).toBe(false)
    })

    it('imageState starts as none', async () => {
      const { useGame } = await import('~/composables/useGame')
      const game = useGame()
      expect(game.imageState.value).toBe('none')
    })

    it('todaysCar selects from the car list deterministically', async () => {
      const { useGame } = await import('~/composables/useGame')
      const game = useGame()
      const car = game.todaysCar.value
      expect(car).toBeDefined()
      expect(car.make).toBeTruthy()
      expect(car.model).toBeTruthy()
      expect(car.year).toBeGreaterThan(0)
    })

    it('has at least 64 cars in the dataset', async () => {
      const { useGame } = await import('~/composables/useGame')
      const game = useGame()
      expect(game.cars.length).toBeGreaterThanOrEqual(64)
    })

    it('generateShareText outputs correct format', async () => {
      const { useGame } = await import('~/composables/useGame')
      const game = useGame()
      const text = game.generateShareText()
      expect(text).toContain('Grille #')
      expect(text).toContain('/6')
      // Should have 6 rows of emojis
      const lines = text.split('\n').filter(l => l.includes('⬜') || l.includes('🟥') || l.includes('✅'))
      expect(lines).toHaveLength(6)
    })
  })
})
