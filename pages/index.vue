<template>
  <div class="min-h-screen bg-gray-950 text-white">
    <header class="relative max-w-lg mx-auto px-4 py-4 flex items-center justify-between">
      <h1 class="flex items-center gap-2 text-2xl font-extrabold tracking-widest uppercase text-white">
        <GrilleLogo :size="32" body-color="white" grill-color="#1f2937" bar-color="#d1d5db" headlight-color="#fbbf24" />
        Grille
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
      <div class="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />
    </header>

    <main class="max-w-lg mx-auto px-4 py-6">
      <p class="text-center text-gray-500 text-xs font-medium tracking-wide mb-4">Puzzle #{{ dayNumber }} · {{ todaysDate }}</p>

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
            v-for="n in MAX_GUESSES"
            :key="n"
            :class="[
              'w-2 h-2 rounded-full transition-all duration-300',
              n <= guessCount
                ? 'bg-white shadow-sm shadow-white/30'
                : 'bg-white/10 border border-white/10',
            ]"
          />
          <span class="ml-2 text-gray-500 text-xs">{{ guessCount }}/{{ MAX_GUESSES }}</span>
        </div>
      </div>

      <ClueGrid :entries="guessEntries" />

      <PostGame
        :open="postGameOpen"
        :car="todaysCar"
        :solved="state.solved"
        @share="share"
        @close="postGameOpen = false"
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

    <footer class="max-w-lg mx-auto px-4 py-8 mt-8">
      <div class="h-px bg-gradient-to-r from-transparent via-white/10 to-transparent mb-6" />
      <div class="flex flex-col items-center gap-3 text-center">
        <GrilleLogo :size="28" headlight-color="#d97706" />
        <p class="text-gray-500 text-xs leading-relaxed max-w-xs">
          A new mystery car every day — guess the exact make and model in 5 tries. Each guess reveals clues and unblurs the image. How well do you know your cars?
        </p>
        <p class="text-gray-600 text-[10px] font-medium tracking-wider uppercase">
          A daily car guessing game
        </p>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useGame, MAX_GUESSES } from '~/composables/useGame'
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

const todaysDate = computed(() => {
  const now = new Date()
  return now.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
})

const statsOpen = ref(false)
const howToPlayOpen = ref(false)
const postGameOpen = ref(false)
const gameStats = ref(loadStats())

watch([() => state.value.solved, () => state.value.failed], ([solved, failed]) => {
  gameStats.value = loadStats()
  if (solved || failed) {
    postGameOpen.value = true
  }
})

onMounted(() => {
  if (import.meta.client) {
    const seen = localStorage.getItem('grille_instructions_seen')
    if (!seen) {
      howToPlayOpen.value = true
    }
    if (state.value.solved || state.value.failed) {
      postGameOpen.value = true
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
