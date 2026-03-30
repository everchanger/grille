import { ref, computed, watch, type Ref } from 'vue'
import type { Car, GameState, GuessFeedback, StatsState, ImageState } from '~/types'
import { useStorage } from '~/composables/useStorage'
import { carLabel } from '~/utils/carLabel'
import carsData from '~/data/cars.json'

const EPOCH = new Date('2025-01-01T00:00:00Z')
export const MAX_GUESSES = 5

/** Return the UTC date string (YYYY-MM-DD) for "today". */
export const getTodayDateStr = (): string => {
  const now = new Date()
  return `${now.getUTCFullYear()}-${String(now.getUTCMonth() + 1).padStart(2, '0')}-${String(now.getUTCDate()).padStart(2, '0')}`
}

/** Convert a YYYY-MM-DD string to a day number (days since EPOCH). */
export const dateToDayNumber = (dateStr: string): number => {
  const parts = dateStr.split('-').map(Number)
  const utc = Date.UTC(parts[0], parts[1] - 1, parts[2])
  return Math.floor((utc - EPOCH.getTime()) / 86400000)
}

/** Convert a day number to a YYYY-MM-DD string. */
export const dayNumberToDate = (day: number): string => {
  const ms = EPOCH.getTime() + day * 86400000
  const d = new Date(ms)
  return `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, '0')}-${String(d.getUTCDate()).padStart(2, '0')}`
}

const CONTINENT_MAP: Record<string, string> = {
  'USA': 'North America',
  'Germany': 'Europe',
  'Japan': 'Asia',
  'Italy': 'Europe',
  'UK': 'Europe',
  'France': 'Europe',
  'Sweden': 'Europe',
  'South Korea': 'Asia',
  'Czech Republic': 'Europe',
  'Spain': 'Europe',
  'Romania': 'Europe',
  'India': 'Asia',
  'China': 'Asia',
  'Australia': 'Oceania',
  'Malaysia': 'Asia',
  'Croatia': 'Europe',
  'Denmark': 'Europe',
  'Lebanon': 'Asia',
}

export const useGame = (dateOverride?: Ref<string | undefined>) => {
  const cars = carsData as Car[]
  const { loadGameState, saveGameState, loadStats, saveStats } = useStorage()

  /** The date string (YYYY-MM-DD) for the puzzle being played. */
  const selectedDateStr = computed<string>(() => {
    return dateOverride?.value || getTodayDateStr()
  })

  const dayNumber = computed<number>(() => {
    return dateToDayNumber(selectedDateStr.value)
  })

  /** Whether we are viewing today's puzzle. */
  const isToday = computed<boolean>(() => {
    return selectedDateStr.value === getTodayDateStr()
  })

  const todaysCar = computed<Car>(() => {
    return cars[dayNumber.value % cars.length]
  })

  const state = ref<GameState>(loadGameState(dateOverride?.value))

  // Reload state when the selected date changes
  if (dateOverride) {
    watch(selectedDateStr, (newDate) => {
      state.value = loadGameState(newDate)
    })
  }

  const guessCount = computed(() => state.value.guesses.filter(g => g !== null).length)

  const BLUR_STEPS = [30, 20, 10, 4]

  const imageState = computed<ImageState>(() => {
    if (state.value.solved || state.value.failed) return 0
    if (guessCount.value === 0) return -1
    return BLUR_STEPS[guessCount.value - 1] ?? 0
  })

  const canGuess = computed(() => !state.value.solved && !state.value.failed)

  const computeFeedback = (guessed: Car, answer: Car): GuessFeedback => {
    const hpDiff = Math.abs(guessed.horsepower - answer.horsepower) / answer.horsepower
    const weightDiff = Math.abs(guessed.weight_kg - answer.weight_kg) / answer.weight_kg

    const sameContinent = (a: string, b: string) =>
      CONTINENT_MAP[a] && CONTINENT_MAP[b] && CONTINENT_MAP[a] === CONTINENT_MAP[b]

    return {
      make:
        guessed.make === answer.make
          ? 'correct'
          : guessed.country === answer.country
            ? 'close'
            : 'wrong',
      model: guessed.model === answer.model ? 'correct' : 'wrong',
      year:
        guessed.year === answer.year
          ? 'correct'
          : guessed.year < answer.year
            ? 'higher'
            : 'lower',
      country:
        guessed.country === answer.country
          ? 'correct'
          : sameContinent(guessed.country, answer.country)
            ? 'close'
            : 'wrong',
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
      if (isToday.value) updateStats(true, idx + 1)
    } else if (idx + 1 >= MAX_GUESSES) {
      state.value.failed = true
      if (isToday.value) updateStats(false, idx + 1)
    }

    saveGameState(state.value, selectedDateStr.value)
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
    const lines: string[] = [`Grille #${dayNumber.value} ${state.value.solved ? filled : 'X'}/${MAX_GUESSES}`, '']
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
    selectedDateStr,
    isToday,
    state,
    guessCount,
    imageState,
    canGuess,
    submitGuess,
    generateShareText,
    computeFeedback,
  }
}
