<template>
  <div class="mt-6 p-5 bg-white/[0.05] backdrop-blur-sm rounded-2xl border border-white/10 ring-1 ring-indigo-500/10 shadow-xl shadow-black/20 animate-fade-in">
    <div class="text-center mb-4">
      <p v-if="solved" class="text-emerald-400 font-bold text-lg animate-slide-in">🎉 You got it!</p>
      <p v-else class="text-red-400 font-bold text-lg animate-slide-in">The answer was...</p>
      <h2 class="text-white text-2xl font-extrabold mt-1 bg-gradient-to-r from-white to-indigo-200 bg-clip-text text-transparent">
        {{ car.make }} {{ car.model }}
      </h2>
      <p class="text-indigo-300/60 text-sm mt-0.5">{{ car.year }} · {{ car.country }}</p>
    </div>

    <img
      :src="resolvedImage"
      :alt="`${car.make} ${car.model}`"
      class="w-full max-w-sm mx-auto rounded-xl mb-4 object-cover h-48 ring-1 ring-white/10"
    />

    <div class="grid grid-cols-2 gap-2 text-sm mb-4">
      <div class="bg-white/[0.05] rounded-lg p-2.5 border border-white/5">
        <span class="text-indigo-400/70 block text-xs">Engine</span>
        <span class="text-white font-semibold">{{ car.engine }}</span>
      </div>
      <div class="bg-white/[0.05] rounded-lg p-2.5 border border-white/5">
        <span class="text-indigo-400/70 block text-xs">Drivetrain</span>
        <span class="text-white font-semibold">{{ car.drivetrain }}</span>
      </div>
      <div class="bg-white/[0.05] rounded-lg p-2.5 border border-white/5">
        <span class="text-indigo-400/70 block text-xs">Horsepower</span>
        <span class="text-white font-semibold">{{ car.horsepower }} hp</span>
      </div>
      <div class="bg-white/[0.05] rounded-lg p-2.5 border border-white/5">
        <span class="text-indigo-400/70 block text-xs">Weight</span>
        <span class="text-white font-semibold">{{ formatWeight(car.weight_kg) }}</span>
      </div>
    </div>

    <p class="text-gray-400 text-sm italic mb-4">{{ car.fact }}</p>

    <div class="flex flex-col gap-2">
      <a
        :href="car.wiki"
        target="_blank"
        rel="noopener noreferrer"
        class="text-indigo-400 text-sm text-center hover:text-indigo-300 transition-colors duration-200"
      >
        Read more ↗
      </a>
      <button
        class="w-full py-2.5 bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 text-white rounded-xl font-semibold text-sm shadow-lg shadow-indigo-500/20 transition-all duration-200 hover:shadow-indigo-500/30"
        @click="$emit('share')"
      >
        📋 Share Result
      </button>
    </div>

    <div class="mt-4 text-center text-gray-500 text-xs">
      <p>Next puzzle in <span class="text-indigo-300 font-semibold">{{ countdown }}</span></p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import type { Car } from '~/types'
import { useUnits } from '~/composables/useUnits'
import { resolveAssetUrl } from '~/utils/useAssetUrl'

const props = defineProps<{
  car: Car
  solved: boolean
}>()

defineEmits<{
  (e: 'share'): void
}>()

const { formatWeight } = useUnits()
const resolvedImage = computed(() => resolveAssetUrl(props.car.image))
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
