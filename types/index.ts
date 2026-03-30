export interface Car {
  id: number
  make: string
  model: string
  year: number
  country: string
  horsepower: number
  weight_kg: number
  engine: string
  drivetrain: string
  image: string
  fact: string
  wiki: string
}

export type FeedbackResult = 'correct' | 'wrong' | 'higher' | 'lower' | 'close_higher' | 'close_lower' | 'close'

export interface GuessFeedback {
  make: FeedbackResult
  model: FeedbackResult
  year: FeedbackResult
  country: FeedbackResult
  horsepower: FeedbackResult
  weight: FeedbackResult
}

export interface GuessEntry {
  car: Car
  feedback: GuessFeedback
}

export interface GameState {
  guesses: (string | null)[]
  guessResults: (GuessFeedback | null)[]
  cluesRevealed: number
  solved: boolean
  failed: boolean
}

export interface StatsState {
  played: number
  wins: number
  currentStreak: number
  maxStreak: number
  guessDistribution: Record<string, number>
}

export interface SettingsState {
  unit: 'kg' | 'lbs'
}

export type ImageState = number
