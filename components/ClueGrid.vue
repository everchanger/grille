<template>
  <div class="w-full">
    <!-- Header row -->
    <div class="grid grid-cols-5 gap-1.5 mb-2">
      <div
        v-for="col in columns"
        :key="col"
        class="text-center text-[10px] font-bold text-indigo-400/70 uppercase tracking-wider"
      >
        {{ col }}
      </div>
    </div>

    <!-- Guess rows -->
    <GuessRow
      v-for="(entry, idx) in filledEntries"
      :key="idx"
      :feedback="entry.feedback"
      :car="entry.car"
      :style="{ animationDelay: `${idx * 60}ms` }"
      class="animate-slide-in opacity-0"
    />

    <!-- Empty rows -->
    <div
      v-for="n in emptyRows"
      :key="`empty-${n}`"
      class="grid grid-cols-5 gap-1.5 mb-1.5"
    >
      <div
        v-for="col in 5"
        :key="col"
        class="min-h-[52px] rounded-lg bg-white/[0.03] border border-dashed border-white/10 transition-colors duration-200"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { GuessEntry } from '~/types'

const props = defineProps<{
  entries: GuessEntry[]
  maxGuesses?: number
}>()

const max = computed(() => props.maxGuesses ?? 6)
const filledEntries = computed(() => props.entries)
const emptyRows = computed(() => Math.max(0, max.value - filledEntries.value.length))
const columns = ['Make', 'Model', 'Year', 'HP', 'Weight']
</script>
