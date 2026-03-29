<template>
  <div class="mt-6 p-4 bg-gray-800 rounded-lg border border-gray-600">
    <div class="text-center mb-4">
      <p v-if="solved" class="text-green-400 font-bold text-lg">🎉 You got it!</p>
      <p v-else class="text-red-400 font-bold text-lg">The answer was...</p>
      <h2 class="text-white text-2xl font-bold mt-1">{{ car.make }} {{ car.model }}</h2>
      <p class="text-gray-400 text-sm">{{ car.year }} · {{ car.country }}</p>
    </div>

    <img
      :src="car.image"
      :alt="`${car.make} ${car.model}`"
      class="w-full max-w-sm mx-auto rounded mb-4 object-cover h-48"
    />

    <div class="grid grid-cols-2 gap-2 text-sm mb-4">
      <div class="bg-gray-700 rounded p-2">
        <span class="text-gray-400 block text-xs">Engine</span>
        <span class="text-white font-semibold">{{ car.engine }}</span>
      </div>
      <div class="bg-gray-700 rounded p-2">
        <span class="text-gray-400 block text-xs">Drivetrain</span>
        <span class="text-white font-semibold">{{ car.drivetrain }}</span>
      </div>
      <div class="bg-gray-700 rounded p-2">
        <span class="text-gray-400 block text-xs">Horsepower</span>
        <span class="text-white font-semibold">{{ car.horsepower }} hp</span>
      </div>
      <div class="bg-gray-700 rounded p-2">
        <span class="text-gray-400 block text-xs">Weight</span>
        <span class="text-white font-semibold">{{ formatWeight(car.weight_kg) }}</span>
      </div>
    </div>

    <p class="text-gray-300 text-sm italic mb-4">{{ car.fact }}</p>

    <div class="flex flex-col gap-2">
      <a
        :href="car.wiki"
        target="_blank"
        rel="noopener noreferrer"
        class="text-blue-400 text-sm text-center hover:underline"
      >
        Read more ↗
      </a>
      <button
        class="w-full py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-semibold text-sm"
        @click="$emit('share')"
      >
        📋 Share Result
      </button>
    </div>

    <div class="mt-4 text-center text-gray-400 text-xs">
      <p>Next puzzle in <span class="text-white font-semibold">{{ countdown }}</span></p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import type { Car } from '~/types'
import { useUnits } from '~/composables/useUnits'

const props = defineProps<{
  car: Car
  solved: boolean
}>()

defineEmits<{
  (e: 'share'): void
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
onUnmounted(() => clearInterval(timer))
</script>
