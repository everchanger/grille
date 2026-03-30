<template>
  <div class="grid grid-cols-6 gap-1.5 mb-1.5">
    <div
      v-for="col in columns"
      :key="col.key"
      :class="['flex flex-col items-center justify-center rounded-lg p-1.5 text-center min-h-[52px] text-xs font-semibold transition-all duration-200 hover:scale-[1.03] hover:brightness-110 ring-1 ring-white/5', cellClass(col.key)]"
    >
      <span class="text-lg leading-none">{{ icon(col.key) }}</span>
      <span class="mt-0.5 text-[10px] opacity-70">{{ col.label }}</span>
      <span v-if="displayValue(col.key)" class="text-[10px] font-bold">{{ displayValue(col.key) }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { GuessFeedback, FeedbackResult } from '~/types'
import { useUnits } from '~/composables/useUnits'

interface Column {
  key: keyof GuessFeedback
  label: string
}

const props = defineProps<{
  feedback: GuessFeedback
  car: import('~/types').Car
}>()

const { formatWeight } = useUnits()

const columns: Column[] = [
  { key: 'make', label: 'Make' },
  { key: 'model', label: 'Model' },
  { key: 'year', label: 'Year' },
  { key: 'country', label: 'Country' },
  { key: 'horsepower', label: 'HP' },
  { key: 'weight', label: 'Weight' },
]

const icon = (key: keyof GuessFeedback): string => {
  const result: FeedbackResult = props.feedback[key]
  if (result === 'correct') return '✅'
  if (result === 'close') return '🟡'
  if (result === 'close_higher') return '🔼'
  if (result === 'close_lower') return '🔽'
  if (result === 'higher') return '🔼'
  if (result === 'lower') return '🔽'
  return '❌'
}

const cellClass = (key: keyof GuessFeedback): string => {
  const result: FeedbackResult = props.feedback[key]
  if (result === 'correct') return 'bg-gradient-to-br from-emerald-600 to-green-700 text-white shadow-sm shadow-green-500/20'
  if (result === 'close' || result === 'close_higher' || result === 'close_lower') return 'bg-gradient-to-br from-amber-500 to-yellow-600 text-white shadow-sm shadow-yellow-500/20'
  return 'bg-white/[0.06] text-gray-300'
}

const displayValue = (key: keyof GuessFeedback): string => {
  if (!props.car) return ''
  if (key === 'make') return props.car.make
  if (key === 'model') return props.car.model
  if (key === 'year') return String(props.car.year)
  if (key === 'country') return props.car.country
  if (key === 'horsepower') return `${props.car.horsepower} hp`
  if (key === 'weight') return formatWeight(props.car.weight_kg)
  return ''
}
</script>
