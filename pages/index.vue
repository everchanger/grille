<template>
  <div class="min-h-screen bg-gray-950 text-white">
    <header class="border-b border-gray-800 px-4 py-3 flex items-center justify-between max-w-lg mx-auto">
      <h1 class="text-xl font-bold tracking-widest uppercase">🚗 Grille</h1>
      <div class="flex items-center gap-3">
        <button
          class="text-gray-400 hover:text-white text-sm font-semibold"
          @click="toggleUnit"
        >
          {{ unit === 'kg' ? 'kg' : 'lbs' }}
        </button>
        <button
          class="text-gray-400 hover:text-white"
          @click="statsOpen = true"
        >
          📊
        </button>
      </div>
    </header>

    <main class="max-w-lg mx-auto px-4 py-6">
      <p class="text-center text-gray-500 text-xs mb-4">Puzzle #{{ dayNumber }}</p>

      <CarImage
        :src="todaysCar.image"
        :alt="`${todaysCar.make} ${todaysCar.model}`"
        :state="imageState"
      />

      <ClueGrid :entries="guessEntries" />

      <div v-if="canGuess" class="mt-4">
        <GuessInput
          :disabled="!canGuess"
          :guessed-ids="guessedCarIds"
          @guess="onGuess"
        />
        <p class="text-center text-gray-500 text-xs mt-2">
          {{ guessCount }}/6 guesses used
        </p>
      </div>

      <PostGame
        v-if="state.solved || state.failed"
        :car="todaysCar"
        :solved="state.solved"
        @share="share"
      />
    </main>

    <StatsModal
      :open="statsOpen"
      :stats="gameStats"
      @close="statsOpen = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useGame } from '~/composables/useGame'
import { useUnits } from '~/composables/useUnits'
import { useStorage } from '~/composables/useStorage'
import type { GuessEntry } from '~/types'
import carsData from '~/data/cars.json'
import type { Car } from '~/types'

const cars = carsData as Car[]
const { todaysCar, dayNumber, state, guessCount, imageState, canGuess, submitGuess, generateShareText } = useGame()
const { unit, toggleUnit } = useUnits()
const { loadStats } = useStorage()

const statsOpen = ref(false)
const gameStats = computed(() => loadStats())

const guessEntries = computed<GuessEntry[]>(() => {
  return state.value.guesses
    .map((name, idx) => {
      if (!name || !state.value.guessResults[idx]) return null
      const car = cars.find(c => `${c.make} ${c.model} (${c.year})` === name || `${c.make} ${c.model}` === name)
      if (!car) return null
      return { car, feedback: state.value.guessResults[idx]! } as GuessEntry
    })
    .filter((e): e is GuessEntry => e !== null)
})

const guessedCarIds = computed(() =>
  guessEntries.value.map(e => e.car.id),
)

const onGuess = (carName: string) => {
  submitGuess(carName)
}

const share = () => {
  const text = generateShareText()
  if (navigator.clipboard) {
    navigator.clipboard.writeText(text).then(() => {
      alert('Copied to clipboard!')
    })
  } else {
    alert(text)
  }
}
</script>
