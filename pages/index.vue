<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-950 via-gray-950 to-indigo-950 text-white">
    <header class="relative max-w-lg mx-auto px-4 py-4 flex items-center justify-between">
      <h1 class="text-2xl font-extrabold tracking-widest uppercase bg-gradient-to-r from-white to-indigo-300 bg-clip-text text-transparent">
        🚗 Grille
      </h1>
      <div class="flex items-center gap-2">
        <button
          class="px-3 py-1 rounded-full text-xs font-semibold bg-white/10 text-gray-300 hover:bg-white/20 hover:text-white backdrop-blur-sm border border-white/10 transition-all duration-200"
          @click="toggleUnit"
        >
          {{ unit === 'kg' ? 'kg' : 'lbs' }}
        </button>
        <button
          class="px-3 py-1 rounded-full text-xs font-semibold bg-white/10 text-gray-300 hover:bg-white/20 hover:text-white backdrop-blur-sm border border-white/10 transition-all duration-200"
          @click="howToPlayOpen = true"
        >
          ❓
        </button>
        <button
          class="px-3 py-1 rounded-full text-xs font-semibold bg-white/10 text-gray-300 hover:bg-white/20 hover:text-white backdrop-blur-sm border border-white/10 transition-all duration-200"
          @click="statsOpen = true"
        >
          📊
        </button>
      </div>
      <div class="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-indigo-500/50 to-transparent" />
    </header>

    <main class="max-w-lg mx-auto px-4 py-6">
      <p class="text-center text-indigo-400/60 text-xs font-medium tracking-wide mb-4">Puzzle #{{ dayNumber }}</p>

      <CarImage
        :src="todaysCar.image"
        :alt="`${todaysCar.make} ${todaysCar.model}`"
        :state="imageState"
      />

      <div v-if="canGuess" class="mt-4 mb-4">
        <GuessInput
          :disabled="!canGuess"
          :guessed-ids="guessedCarIds"
          @guess="onGuess"
        />
        <div class="mt-3 flex items-center justify-center gap-1.5">
          <div
            v-for="n in 6"
            :key="n"
            :class="[
              'w-2 h-2 rounded-full transition-all duration-300',
              n <= guessCount
                ? 'bg-indigo-500 shadow-sm shadow-indigo-500/50'
                : 'bg-white/10 border border-white/10',
            ]"
          />
          <span class="ml-2 text-gray-500 text-xs">{{ guessCount }}/6</span>
        </div>
      </div>

      <ClueGrid :entries="guessEntries" />

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

    <HowToPlay
      :open="howToPlayOpen"
      @close="howToPlayOpen = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useGame } from '~/composables/useGame'
import { useUnits } from '~/composables/useUnits'
import { useStorage } from '~/composables/useStorage'
import { carLabel } from '~/utils/carLabel'
import type { GuessEntry } from '~/types'
import carsData from '~/data/cars.json'
import type { Car } from '~/types'

const cars = carsData as Car[]
const { todaysCar, dayNumber, state, guessCount, imageState, canGuess, submitGuess, generateShareText } = useGame()
const { unit, toggleUnit } = useUnits()
const { loadStats } = useStorage()

const statsOpen = ref(false)
const howToPlayOpen = ref(false)
const gameStats = computed(() => loadStats())

onMounted(() => {
  if (import.meta.client) {
    const seen = localStorage.getItem('grille_instructions_seen')
    if (!seen) {
      howToPlayOpen.value = true
    }
  }
})

const guessEntries = computed<GuessEntry[]>(() => {
  return state.value.guesses
    .map((name, idx) => {
      if (!name || !state.value.guessResults[idx]) return null
      const car = cars.find(c => carLabel(c) === name || `${c.make} ${c.model}` === name)
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
