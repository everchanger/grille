<template>
  <div
    v-if="open"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/70"
    @click.self="$emit('close')"
  >
    <div class="bg-gray-900 rounded-xl p-6 w-full max-w-sm mx-4 border border-gray-700">
      <div class="flex justify-between items-center mb-4">
        <h2 class="text-white font-bold text-lg">📊 Statistics</h2>
        <button class="text-gray-400 hover:text-white text-xl" @click="$emit('close')">✕</button>
      </div>

      <div class="grid grid-cols-4 gap-2 mb-6">
        <div class="text-center">
          <p class="text-white text-2xl font-bold">{{ stats.played }}</p>
          <p class="text-gray-400 text-xs">Played</p>
        </div>
        <div class="text-center">
          <p class="text-white text-2xl font-bold">{{ winPercent }}%</p>
          <p class="text-gray-400 text-xs">Win %</p>
        </div>
        <div class="text-center">
          <p class="text-white text-2xl font-bold">{{ stats.currentStreak }}</p>
          <p class="text-gray-400 text-xs">Streak</p>
        </div>
        <div class="text-center">
          <p class="text-white text-2xl font-bold">{{ stats.maxStreak }}</p>
          <p class="text-gray-400 text-xs">Best</p>
        </div>
      </div>

      <h3 class="text-gray-400 text-xs uppercase tracking-wide mb-2">Guess Distribution</h3>
      <div class="space-y-1">
        <div
          v-for="n in 6"
          :key="n"
          class="flex items-center gap-2"
        >
          <span class="text-gray-400 text-xs w-3">{{ n }}</span>
          <div class="flex-1 bg-gray-800 rounded overflow-hidden h-5">
            <div
              class="bg-blue-600 h-full flex items-center justify-end pr-1"
              :style="{ width: barWidth(n) }"
            >
              <span class="text-white text-xs">{{ stats.guessDistribution[n] ?? 0 }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { StatsState } from '~/types'

const props = defineProps<{
  open: boolean
  stats: StatsState
}>()

defineEmits<{
  (e: 'close'): void
}>()

const winPercent = computed(() =>
  props.stats.played === 0 ? 0 : Math.round((props.stats.wins / props.stats.played) * 100),
)

const maxDist = computed(() =>
  Math.max(1, ...Object.values(props.stats.guessDistribution)),
)

const barWidth = (n: number): string => {
  const val = props.stats.guessDistribution[n] ?? 0
  return `${Math.max(5, (val / maxDist.value) * 100)}%`
}
</script>
