<template>
  <div class="w-full">
    <!-- Header row -->
    <div class="grid grid-cols-5 gap-1 mb-2">
      <div
        v-for="col in columns"
        :key="col"
        class="text-center text-xs font-bold text-gray-400 uppercase tracking-wide"
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
    />

    <!-- Empty rows -->
    <div
      v-for="n in emptyRows"
      :key="`empty-${n}`"
      class="grid grid-cols-5 gap-1 mb-1"
    >
      <div
        v-for="col in 5"
        :key="col"
        class="min-h-[52px] rounded bg-gray-800 border border-gray-700"
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
