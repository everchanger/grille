<template>
  <div class="w-full max-w-md mx-auto my-4 rounded overflow-hidden bg-gray-800">
    <template v-if="state === 'none'">
      <div class="h-48 flex items-center justify-center text-gray-500 text-4xl">🚗</div>
    </template>
    <template v-else-if="state === 'silhouette'">
      <div class="relative h-48">
        <img
          :src="resolvedSrc"
          :alt="alt"
          class="w-full h-full object-cover"
          style="filter: brightness(0) contrast(1);"
        />
      </div>
    </template>
    <template v-else-if="state === 'blurred'">
      <div class="relative h-48">
        <img
          :src="resolvedSrc"
          :alt="alt"
          class="w-full h-full object-cover"
          style="filter: blur(12px);"
        />
      </div>
    </template>
    <template v-else>
      <img
        :src="resolvedSrc"
        :alt="alt"
        class="w-full h-48 object-cover"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ImageState } from '~/types'
import { resolveAssetUrl } from '~/utils/useAssetUrl'

const props = defineProps<{
  src: string
  alt: string
  state: ImageState
}>()

const resolvedSrc = computed(() => resolveAssetUrl(props.src))
</script>
