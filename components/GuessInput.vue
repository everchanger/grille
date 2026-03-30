<template>
  <div class="relative w-full">
    <input
      v-model="query"
      type="text"
      placeholder="Search for a car..."
      class="w-full px-4 py-2.5 rounded-xl bg-white/[0.06] text-white placeholder-gray-500 border border-white/10 focus:outline-none focus:ring-2 focus:ring-white/25 focus:border-white/25 backdrop-blur-sm transition-all duration-200"
      :disabled="disabled"
      @input="onInput"
      @keydown.enter="selectFirst"
      @keydown.escape="close"
    />
    <ul
      v-if="suggestions.length > 0"
      class="absolute z-10 w-full bg-gray-900/90 backdrop-blur-xl border border-white/10 rounded-xl mt-2 max-h-60 overflow-y-auto shadow-xl shadow-black/40 animate-scale-in"
    >
      <li
        v-for="car in suggestions"
        :key="car.id"
        class="px-4 py-2.5 cursor-pointer text-gray-300 text-sm hover:bg-white/10 hover:text-white transition-colors duration-150 first:rounded-t-xl last:rounded-b-xl"
        @mousedown.prevent="select(car)"
      >
        {{ car.make }} {{ car.model }} <span class="text-gray-500">({{ car.year }})</span>
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
