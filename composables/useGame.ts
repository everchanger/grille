import { ref, computed } from 'vue'
import type { Car, GameState, GuessFeedback, StatsState, ImageState } from '~/types'
import { useStorage } from '~/composables/useStorage'
import { carLabel } from '~/utils/carLabel'
import carsData from '~/data/cars.json'

const EPOCH = new Date('2025-01-01T00:00:00Z')
const MAX_GUESSES = 6

export const useGame = () => {
  const cars = carsData as Car[]
  const { loadGameState, saveGameState, loadStats, saveStats } = useStorage()

  const dayNumber = computed<number>(() => {
    const now = new Date()
    const utcNow = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate())
    return Math.floor((utcNow - EPOCH.getTime()) / 86400000)
  })

  const todaysCar = computed<Car>(() => {
    return cars[dayNumber.value % cars.length]
  })

  const state = ref<GameState>(loadGameState())

  const guessCount = computed(() => state.value.guesses.filter(g => g !== null).length)

  const BLUR_STEPS = [40, 30, 20, 12, 6, 3]

  const imageState = computed<ImageState>(() => {
    if (state.value.solved || state.value.failed) return 0
    return BLUR_STEPS[guessCount.value] ?? 0
  })

  const canGuess = computed(() => !state.value.solved && !state.value.failed)

  const computeFeedback = (guessed: Car, answer: Car): GuessFeedback => {
    const hpDiff = Math.abs(guessed.horsepower - answer.horsepower) / answer.horsepower
    const weightDiff = Math.abs(guessed.weight_kg - answer.weight_kg) / answer.weight_kg

    return {
      make: guessed.make === answer.make ? 'correct' : 'wrong',
      model: guessed.model === answer.model ? 'correct' : 'wrong',
      year:
        guessed.year === answer.year
          ? 'correct'
          : guessed.year < answer.year
            ? 'higher'
            : 'lower',
      country: guessed.country === answer.country ? 'correct' : 'wrong',
      horsepower:
        guessed.horsepower === answer.horsepower
          ? 'correct'
          : hpDiff <= 0.15
            ? (guessed.horsepower < answer.horsepower ? 'close_higher' : 'close_lower')
            : guessed.horsepower < answer.horsepower
              ? 'higher'
              : 'lower',
      weight:
        guessed.weight_kg === answer.weight_kg
          ? 'correct'
          : weightDiff <= 0.1
            ? (guessed.weight_kg < answer.weight_kg ? 'close_higher' : 'close_lower')
            : guessed.weight_kg < answer.weight_kg
              ? 'higher'
              : 'lower',
    }
  }

  const submitGuess = (carName: string) => {
    if (!canGuess.value) return

    const guessed = cars.find(
      c => carLabel(c) === carName || `${c.make} ${c.model}` === carName,
    )
    if (!guessed) return

    const idx = guessCount.value
    const feedback = computeFeedback(guessed, todaysCar.value)

    state.value.guesses[idx] = carName
    state.value.guessResults[idx] = feedback

    const solved = feedback.make === 'correct' &&
      feedback.model === 'correct' &&
      feedback.year === 'correct' &&
      feedback.country === 'correct' &&
      feedback.horsepower === 'correct' &&
      feedback.weight === 'correct'

    if (solved) {
      state.value.solved = true
      updateStats(true, idx + 1)
    } else if (idx + 1 >= MAX_GUESSES) {
      state.value.failed = true
      updateStats(false, idx + 1)
    }

    saveGameState(state.value)
  }

  const updateStats = (won: boolean, guessNum: number) => {
    const stats: StatsState = loadStats()
    stats.played += 1
    if (won) {
      stats.wins += 1
      stats.currentStreak += 1
      if (stats.currentStreak > stats.maxStreak) stats.maxStreak = stats.currentStreak
      const key = String(guessNum)
      stats.guessDistribution[key] = (stats.guessDistribution[key] ?? 0) + 1
    } else {
      stats.currentStreak = 0
    }
    saveStats(stats)
  }

  const generateShareText = (): string => {
    const filled = state.value.guesses.filter(g => g !== null).length
    const lines: string[] = [`Grille #${dayNumber.value} ${state.value.solved ? filled : 'X'}/6`, '']
    const row = (idx: number) => {
      if (state.value.guesses[idx] === null) return '⬜⬜⬜⬜⬜⬜'
      return state.value.solved && state.value.guesses[idx] !== null && idx === filled - 1
        ? '✅✅✅✅✅✅'
        : '🟥🟥🟥🟥🟥🟥'
    }
    for (let i = 0; i < MAX_GUESSES; i++) lines.push(row(i))
    return lines.join('\n')
  }

  return {
    cars,
    todaysCar,
    dayNumber,
    state,
    guessCount,
    imageState,
    canGuess,
    submitGuess,
    generateShareText,
    computeFeedback,
  }
}
