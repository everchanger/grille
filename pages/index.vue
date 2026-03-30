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
            <span
              v-if="state.solved"
              class="ml-1.5 text-emerald-400"
              title="Solved"
            >✓</span>
            <span
              v-else-if="state.failed"
              class="ml-1.5 text-red-400"
              title="Failed"
            >✗</span>
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
        :car-name="gameComplete ? `${todaysCar.make} ${todaysCar.model}` : undefined"
        :car-subtitle="gameComplete ? `${todaysCar.year} · ${todaysCar.country}` : undefined"
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

      <!-- Completion banner -->
      <Transition name="banner">
        <div
          v-if="gameComplete"
          :class="[
            'text-center py-3 mb-4 rounded-xl border animate-slide-in',
            state.solved
              ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
              : 'bg-red-500/10 border-red-500/20 text-red-400',
          ]"
        >
          <p class="font-bold text-lg">
            {{ state.solved ? '🎉 You got it!' : 'The answer was...' }}
          </p>
          <p class="text-white text-xl font-extrabold mt-0.5">
            {{ todaysCar.make }} {{ todaysCar.model }}
          </p>
        </div>
      </Transition>

      <!-- Tabs -->
      <div class="flex gap-1 mb-4 bg-white/[0.04] rounded-xl p-1 border border-white/5">
        <button
          :class="[
            'flex-1 py-2 px-3 rounded-lg text-sm font-semibold transition-all duration-300',
            activeTab === 'guesses'
              ? 'bg-white/10 text-white shadow-sm shadow-white/5'
              : 'text-gray-500 hover:text-gray-300 hover:bg-white/[0.04]',
          ]"
          @click="activeTab = 'guesses'"
        >
          Guesses
        </button>
        <button
          :class="[
            'flex-1 py-2 px-3 rounded-lg text-sm font-semibold transition-all duration-300',
            activeTab === 'details'
              ? 'bg-white/10 text-white shadow-sm shadow-white/5'
              : 'text-gray-500 hover:text-gray-300 hover:bg-white/[0.04]',
          ]"
          @click="activeTab = 'details'"
        >
          Details
        </button>
      </div>

      <!-- Tab content with crossfade -->
      <div class="relative">
        <Transition name="tab-fade" mode="out-in">
          <div v-if="activeTab === 'guesses'" key="guesses">
            <ClueGrid :entries="guessEntries" />
          </div>
          <div v-else key="details">
            <ResultDetails
              :car="todaysCar"
              :blurred="!gameComplete"
              :is-today="isToday"
              @share="share"
              @go-to-today="goToToday"
            />
          </div>
        </Transition>
      </div>
    </main>

    <!-- Confetti canvas (fires only on fresh solve) -->
    <canvas
      v-if="showConfetti"
      ref="confettiCanvas"
      class="fixed inset-0 pointer-events-none z-[60]"
    />

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

<style scoped>
.tab-fade-enter-active,
.tab-fade-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.tab-fade-enter-from {
  opacity: 0;
  transform: translateY(6px);
}
.tab-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
.banner-enter-active {
  transition: opacity 0.4s ease, transform 0.4s ease;
}
.banner-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.banner-enter-from {
  opacity: 0;
  transform: scale(0.95) translateY(-8px);
}
.banner-leave-to {
  opacity: 0;
  transform: scale(0.95);
}
</style>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
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
const gameStats = ref(loadStats())

const gameComplete = computed(() => state.value.solved || state.value.failed)

// Tab state: "guesses" when playing, "details" when complete
const activeTab = ref<'guesses' | 'details'>(gameComplete.value ? 'details' : 'guesses')

// Animation timing constants
const TAB_SWITCH_DELAY_MS = 600
const CONFETTI_LAUNCH_DELAY_MS = 400
const CONFETTI_DURATION_MS = 5000
const CONFETTI_PARTICLE_COUNT = 100

const showConfetti = ref(false)
const confettiCanvas = ref<HTMLCanvasElement | null>(null)
let confettiCleanupTimer: ReturnType<typeof setTimeout> | undefined
let confettiAnimId: number | undefined
// Guard flag: when true, a date navigation caused the state change, not a fresh solve
let isNavigating = false

// When navigating between dates, reset tab based on game state
watch(selectedDateStr, () => {
  isNavigating = true
  showConfetti.value = false
  nextTick(() => {
    activeTab.value = gameComplete.value ? 'details' : 'guesses'
    isNavigating = false
  })
})

// Watch for game completion (fresh solve/fail)
watch([() => state.value.solved, () => state.value.failed], ([solved, failed]) => {
  gameStats.value = loadStats()
  if (solved || failed) {
    // Switch to details tab with a small delay for animation
    setTimeout(() => {
      activeTab.value = 'details'
    }, TAB_SWITCH_DELAY_MS)
    // Fire confetti only on fresh win, not when loading a previously-solved puzzle
    if (solved && !isNavigating) {
      showConfetti.value = true
      nextTick(() => {
        setTimeout(launchConfetti, CONFETTI_LAUNCH_DELAY_MS)
      })
    }
  }
})

onMounted(() => {
  if (import.meta.client) {
    const seen = localStorage.getItem('grille_instructions_seen')
    if (!seen) {
      howToPlayOpen.value = true
    }
    // If the game was already complete, default to details tab (no confetti)
    if (gameComplete.value) {
      activeTab.value = 'details'
    }
  }
})

onUnmounted(() => {
  if (confettiCleanupTimer) clearTimeout(confettiCleanupTimer)
  if (confettiAnimId) cancelAnimationFrame(confettiAnimId)
})

// Confetti effect
interface Particle {
  x: number
  y: number
  vx: number
  vy: number
  size: number
  color: string
  rotation: number
  rotationSpeed: number
  opacity: number
}

const launchConfetti = () => {
  const canvas = confettiCanvas.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  canvas.width = window.innerWidth
  canvas.height = window.innerHeight

  const colors = ['#6366f1', '#818cf8', '#34d399', '#fbbf24', '#f87171', '#a78bfa', '#38bdf8', '#fb923c']
  const particles: Particle[] = []

  for (let i = 0; i < CONFETTI_PARTICLE_COUNT; i++) {
    particles.push({
      x: canvas.width / 2 + (Math.random() - 0.5) * 200,
      y: canvas.height * 0.4,
      vx: (Math.random() - 0.5) * 15,
      vy: -Math.random() * 18 - 5,
      size: Math.random() * 8 + 4,
      color: colors[Math.floor(Math.random() * colors.length)],
      rotation: Math.random() * 360,
      rotationSpeed: (Math.random() - 0.5) * 10,
      opacity: 1,
    })
  }

  let animId: number
  const gravity = 0.4
  const drag = 0.99

  const animate = () => {
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    let alive = false

    for (const p of particles) {
      p.vy += gravity
      p.vx *= drag
      p.x += p.vx
      p.y += p.vy
      p.rotation += p.rotationSpeed
      p.opacity -= 0.005

      if (p.opacity <= 0) continue
      alive = true

      ctx.save()
      ctx.globalAlpha = p.opacity
      ctx.translate(p.x, p.y)
      ctx.rotate((p.rotation * Math.PI) / 180)
      ctx.fillStyle = p.color
      ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size * 0.6)
      ctx.restore()
    }

    if (alive) {
      animId = requestAnimationFrame(animate)
    } else {
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      showConfetti.value = false
    }
  }

  animId = requestAnimationFrame(animate)
  confettiAnimId = animId

  confettiCleanupTimer = setTimeout(() => {
    cancelAnimationFrame(animId)
    if (ctx) ctx.clearRect(0, 0, canvas.width, canvas.height)
    showConfetti.value = false
  }, CONFETTI_DURATION_MS)
}

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
  const origin = window.location.origin
  const baseURL = useRuntimeConfig().app.baseURL || '/'
  const base = `${origin}${baseURL}`
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
