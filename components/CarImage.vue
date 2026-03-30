<template>
  <div class="w-full max-w-md mx-auto my-4 rounded-xl overflow-hidden bg-gray-800/50 backdrop-blur-sm ring-1 ring-white/10 shadow-lg shadow-black/20 transition-all duration-300">
    <template v-if="state < 0">
      <div class="h-48 flex flex-col items-center justify-center bg-gradient-to-br from-gray-800/80 to-gray-900/80 gap-2">
        <GrilleLogo :size="56" :animate="true" class="opacity-40" />
        <span class="text-gray-500 text-xs font-medium">Make a guess to reveal the image</span>
      </div>
    </template>
    <template v-else-if="imageError">
      <div class="h-48 flex items-center justify-center bg-gradient-to-br from-gray-800/50 to-gray-900/50">
        <GrilleLogo :size="48" headlight-color="#d97706" />
      </div>
    </template>
    <template v-else>
      <img
        :src="resolvedSrc"
        :alt="alt"
        class="w-full h-48 object-cover transition-[filter] duration-500"
        :style="state > 0 ? `filter: blur(${state}px)` : undefined"
        @error="onImageError"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { ImageState } from '~/types'
import { resolveAssetUrl } from '~/utils/useAssetUrl'

const props = defineProps<{
  src: string
  alt: string
  state: ImageState
}>()

const imageError = ref(false)

const resolvedSrc = computed(() => resolveAssetUrl(props.src))

const onImageError = () => {
  imageError.value = true
}

watch(() => props.src, () => {
  imageError.value = false
})
</script>
