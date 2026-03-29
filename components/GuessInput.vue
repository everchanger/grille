<template>
  <div class="relative w-full">
    <input
      v-model="query"
      type="text"
      placeholder="Search for a car..."
      class="w-full px-4 py-2 rounded bg-gray-800 text-white border border-gray-600 focus:outline-none focus:border-blue-400"
      :disabled="disabled"
      @input="onInput"
      @keydown.enter="selectFirst"
      @keydown.escape="close"
    />
    <ul
      v-if="suggestions.length > 0"
      class="absolute z-10 w-full bg-gray-800 border border-gray-600 rounded mt-1 max-h-60 overflow-y-auto"
    >
      <li
        v-for="car in suggestions"
        :key="car.id"
        class="px-4 py-2 cursor-pointer hover:bg-gray-700 text-white text-sm"
        @mousedown.prevent="select(car)"
      >
        {{ car.make }} {{ car.model }} ({{ car.year }})
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Car } from '~/types'
import { carLabel } from '~/utils/carLabel'
import carsData from '~/data/cars.json'

const props = defineProps<{
  disabled?: boolean
  guessedIds?: number[]
}>()

const emit = defineEmits<{
  (e: 'guess', value: string): void
}>()

const cars = carsData as Car[]
const query = ref('')

const suggestions = computed<Car[]>(() => {
  if (!query.value.trim()) return []
  const q = query.value.toLowerCase()
  return cars
    .filter(c => !(props.guessedIds ?? []).includes(c.id))
    .filter(c => {
      const full = `${c.make} ${c.model} ${c.year}`.toLowerCase()
      return full.includes(q)
    })
    .slice(0, 8)
})

const onInput = () => {
  // suggestions are reactive
}

const select = (car: Car) => {
  query.value = carLabel(car)
  emit('guess', query.value)
  query.value = ''
}

const selectFirst = () => {
  if (suggestions.value.length > 0) select(suggestions.value[0])
}

const close = () => {
  query.value = ''
}
</script>
