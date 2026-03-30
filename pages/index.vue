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
      <!-- Date navigation -->
      <div class="flex items-center justify-center gap-3 mb-4">
        <button
          class="p-1.5 rounded-full bg-white/10 text-gray-300 hover:bg-white/20 hover:text-white border border-white/10 transition-all duration-200"
          title="Previous day"
          @click="goToPreviousDay"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd" /></svg>
        </button>

        <div class="relative">
          <button
            class="px-3 py-1 rounded-lg text-xs font-medium text-gray-400 hover:text-white bg-white/[0.06] hover:bg-white/10 border border-white/10 transition-all duration-200 cursor-pointer"
            title="Pick a date"
            @click="openDatePicker"
          >
            <span class="text-gray-500 text-[10px] tracking-wider uppercase">Puzzle #{{ dayNumber }}</span>
            <span class="mx-1.5 text-gray-600">·</span>
            <span>{{ displayDate }}</span>
          </button>
          <input
            ref="datePickerRef"
            type="date"
            :value="selectedDateStr"
            :min="epochDateStr"
            :max="todayDateStr"
            class="absolute inset-0 opacity-0 w-full h-full cursor-pointer"
            @change="onDatePick"
          />
        </div>

        <button
          v-if="!isToday"
          class="p-1.5 rounded-full bg-white/10 text-gray-300 hover:bg-white/20 hover:text-white border border-white/10 transition-all duration-200"
          title="Next day"
          @click="goToNextDay"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" /></svg>
        </button>
        <div v-else class="w-[30px]" />

        <button
          v-if="!isToday"
          class="px-2.5 py-1 rounded-full text-[10px] font-semibold bg-indigo-500/20 text-indigo-300 hover:bg-indigo-500/30 hover:text-indigo-200 border border-indigo-500/30 transition-all duration-200"
          @click="goToToday"
        >
          Today
        </button>
      </div>

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
        :is-today="isToday"
        @share="share"
        @close="postGameOpen = false"
        @go-to-today="goToToday"
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
import { useRoute, useRouter } from 'vue-router'
import { useGame, MAX_GUESSES, getTodayDateStr, dateToDayNumber, dayNumberToDate } from '~/composables/useGame'
import { useUnits } from '~/composables/useUnits'
import { useStorage } from '~/composables/useStorage'
import { carLabel } from '~/utils/carLabel'
import type { GuessEntry } from '~/types'
import carsData from '~/data/cars.json'
import type { Car } from '~/types'

const cars = carsData as Car[]
const route = useRoute()
const router = useRouter()

const epochDateStr = '2025-01-01'
const todayDateStr = computed(() => getTodayDateStr())

// Read date from query param, validate it
const dateFromQuery = computed<string | undefined>(() => {
  const q = route.query.date
  if (!q || typeof q !== 'string') return undefined
  // Validate format YYYY-MM-DD
  if (!/^\d{4}-\d{2}-\d{2}$/.test(q)) return undefined
  // Validate it's not in the future and not before epoch
  if (q > todayDateStr.value) return undefined
  if (q < epochDateStr) return undefined
  // Validate it's a real date
  const [y, m, d] = q.split('-').map(Number)
  const date = new Date(Date.UTC(y, m - 1, d))
  if (date.getUTCFullYear() !== y || date.getUTCMonth() !== m - 1 || date.getUTCDate() !== d) return undefined
  // If the date is today, treat as no override (canonical URL)
  if (q === todayDateStr.value) return undefined
  return q
})

const { todaysCar, dayNumber, selectedDateStr, isToday, state, guessCount, imageState, canGuess, submitGuess, generateShareText } = useGame(dateFromQuery)
const { unit, toggleUnit } = useUnits()
const { loadStats } = useStorage()

const displayDate = computed(() => {
  const [y, m, d] = selectedDateStr.value.split('-').map(Number)
  const date = new Date(Date.UTC(y, m - 1, d))
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' })
})

const datePickerRef = ref<HTMLInputElement | null>(null)

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

// Close post-game modal when navigating to a different date
watch(selectedDateStr, () => {
  postGameOpen.value = false
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

// Date navigation
const navigateToDate = (dateStr: string) => {
  if (dateStr === getTodayDateStr()) {
    router.push({ query: {} })
  } else {
    router.push({ query: { date: dateStr } })
  }
}

const goToPreviousDay = () => {
  const prevDay = dayNumber.value - 1
  if (prevDay < 0) return
  navigateToDate(dayNumberToDate(prevDay))
}

const goToNextDay = () => {
  const todayDayNum = dateToDayNumber(getTodayDateStr())
  if (dayNumber.value >= todayDayNum) return
  navigateToDate(dayNumberToDate(dayNumber.value + 1))
}

const goToToday = () => {
  navigateToDate(getTodayDateStr())
}

const openDatePicker = () => {
  datePickerRef.value?.showPicker?.()
}

const onDatePick = (event: Event) => {
  const input = event.target as HTMLInputElement
  if (input.value) {
    navigateToDate(input.value)
  }
}

const share = () => {
  let text = generateShareText()
  // Add the puzzle URL so friends can play the same day
  const base = 'https://everchanger.github.io/grille/'
  const url = isToday.value ? base : `${base}?date=${selectedDateStr.value}`
  text += `\n${url}`
  if (navigator.clipboard) {
    navigator.clipboard.writeText(text).then(() => {
      alert('Copied to clipboard!')
    })
  } else {
    alert(text)
  }
}
</script>
