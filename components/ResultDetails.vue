<template>
  <div class="w-full">
    <div
      :class="[
        'transition-all duration-500',
        blurred ? 'blur-md select-none pointer-events-none' : '',
      ]"
    >
      <!-- Car specs grid -->
      <div class="grid grid-cols-2 gap-2 text-sm mb-4">
        <div class="bg-white/[0.05] rounded-lg p-2.5 border border-white/5">
          <span class="text-gray-500 block text-xs">Engine</span>
          <span class="text-white font-semibold">{{ car.engine }}</span>
        </div>
        <div class="bg-white/[0.05] rounded-lg p-2.5 border border-white/5">
          <span class="text-gray-500 block text-xs">Drivetrain</span>
          <span class="text-white font-semibold">{{ car.drivetrain }}</span>
        </div>
        <div class="bg-white/[0.05] rounded-lg p-2.5 border border-white/5">
          <span class="text-gray-500 block text-xs">Horsepower</span>
          <span class="text-white font-semibold">{{ car.horsepower }} hp</span>
        </div>
        <div class="bg-white/[0.05] rounded-lg p-2.5 border border-white/5">
          <span class="text-gray-500 block text-xs">Weight</span>
          <span class="text-white font-semibold">{{ formatWeight(car.weight_kg) }}</span>
        </div>
        <div class="bg-white/[0.05] rounded-lg p-2.5 border border-white/5">
          <span class="text-gray-500 block text-xs">Year</span>
          <span class="text-white font-semibold">{{ car.year }}</span>
        </div>
        <div class="bg-white/[0.05] rounded-lg p-2.5 border border-white/5">
          <span class="text-gray-500 block text-xs">Country</span>
          <span class="text-white font-semibold">{{ car.country }}</span>
        </div>
      </div>

      <!-- Fun fact -->
      <p class="text-gray-400 text-sm italic mb-4">{{ car.fact }}</p>

      <!-- Actions -->
      <div class="flex flex-col gap-2">
        <a
          :href="car.wiki"
          target="_blank"
          rel="noopener noreferrer"
          class="text-gray-400 text-sm text-center hover:text-white transition-colors duration-200"
        >
          Read more on Wikipedia ↗
        </a>
        <button
          class="w-full py-2.5 bg-white hover:bg-gray-200 text-gray-900 rounded-xl font-semibold text-sm shadow-lg shadow-black/20 transition-all duration-200"
          @click="$emit('share')"
        >
          📋 Share Result
        </button>
        <button
          v-if="!isToday"
          class="w-full py-2.5 bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-300 rounded-xl font-semibold text-sm border border-indigo-500/30 transition-all duration-200"
          @click="$emit('goToToday')"
        >
          ▶ Play Today's Puzzle
        </button>
      </div>

      <!-- Next puzzle countdown -->
      <div v-if="isToday" class="mt-4 text-center text-gray-500 text-xs">
        <p>Next puzzle in <span class="text-white font-semibold">{{ countdown }}</span></p>
      </div>
    </div>

    <!-- Blurred hint text -->
    <p v-if="blurred" class="text-center text-gray-600 text-xs mt-3">
      Complete the puzzle to reveal car details
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import type { Car } from '~/types'
import { useUnits } from '~/composables/useUnits'

defineProps<{
  car: Car
  blurred: boolean
  isToday: boolean
}>()

defineEmits<{
  (e: 'share'): void
  (e: 'goToToday'): void
}>()

const { formatWeight } = useUnits()
const countdown = ref('')

const updateCountdown = () => {
  const now = new Date()
  const tomorrow = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() + 1))
  const diff = tomorrow.getTime() - now.getTime()
  const h = Math.floor(diff / 3600000)
  const m = Math.floor((diff % 3600000) / 60000)
  const s = Math.floor((diff % 60000) / 1000)
  countdown.value = `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

let timer: ReturnType<typeof setInterval>

onMounted(() => {
  updateCountdown()
  timer = setInterval(updateCountdown, 1000)
})

onUnmounted(() => {
  clearInterval(timer)
})
</script>
