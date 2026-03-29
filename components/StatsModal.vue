<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="open"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
        @click.self="$emit('close')"
      >
        <div class="bg-gray-900/90 backdrop-blur-xl rounded-2xl p-6 w-full max-w-sm mx-4 border border-white/10 ring-1 ring-indigo-500/10 shadow-2xl shadow-black/40 animate-scale-in">
          <div class="flex justify-between items-center mb-5">
            <h2 class="text-white font-extrabold text-lg bg-gradient-to-r from-white to-indigo-300 bg-clip-text text-transparent">📊 Statistics</h2>
            <button class="text-gray-500 hover:text-white text-xl transition-colors duration-200" @click="$emit('close')">✕</button>
          </div>

          <div class="grid grid-cols-4 gap-2 mb-6">
            <div class="text-center p-2 rounded-lg bg-white/[0.04]">
              <p class="text-white text-2xl font-extrabold">{{ stats.played }}</p>
              <p class="text-indigo-400/60 text-[10px] font-medium uppercase tracking-wider">Played</p>
            </div>
            <div class="text-center p-2 rounded-lg bg-white/[0.04]">
              <p class="text-white text-2xl font-extrabold">{{ winPercent }}%</p>
              <p class="text-indigo-400/60 text-[10px] font-medium uppercase tracking-wider">Win %</p>
            </div>
            <div class="text-center p-2 rounded-lg bg-white/[0.04]">
              <p class="text-white text-2xl font-extrabold">{{ stats.currentStreak }}</p>
              <p class="text-indigo-400/60 text-[10px] font-medium uppercase tracking-wider">Streak</p>
            </div>
            <div class="text-center p-2 rounded-lg bg-white/[0.04]">
              <p class="text-white text-2xl font-extrabold">{{ stats.maxStreak }}</p>
              <p class="text-indigo-400/60 text-[10px] font-medium uppercase tracking-wider">Best</p>
            </div>
          </div>

          <h3 class="text-indigo-400/60 text-[10px] font-bold uppercase tracking-wider mb-3">Guess Distribution</h3>
          <div class="space-y-1.5">
            <div
              v-for="n in 6"
              :key="n"
              class="flex items-center gap-2"
            >
              <span class="text-gray-500 text-xs w-3 font-medium">{{ n }}</span>
              <div class="flex-1 bg-white/[0.04] rounded-md overflow-hidden h-6">
                <div
                  class="bg-gradient-to-r from-indigo-600 to-blue-500 h-full flex items-center justify-end pr-2 rounded-md transition-all duration-500"
                  :style="{ width: barWidth(n) }"
                >
                  <span class="text-white text-xs font-semibold">{{ stats.guessDistribution[n] ?? 0 }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}
.modal-enter-active > div,
.modal-leave-active > div {
  transition: transform 0.2s ease, opacity 0.2s ease;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
.modal-enter-from > div,
.modal-leave-to > div {
  transform: scale(0.95);
  opacity: 0;
}
</style>

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
