<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 64 64"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    :class="className"
  >
    <!-- Outer car silhouette -->
    <path
      d="M8 36 C8 30 14 22 20 20 L24 16 C28 12 36 12 40 16 L44 20 C50 22 56 30 56 36 L56 42 C56 44 54 46 52 46 L12 46 C10 46 8 44 8 42 Z"
      :fill="bodyColor"
    />
    <!-- Grille -->
    <rect x="22" y="30" width="20" height="12" rx="2" :fill="grillColor" />
    <!-- Grille horizontal bars -->
    <line x1="22" y1="33" x2="42" y2="33" :stroke="barColor" stroke-width="1.2" />
    <line x1="22" y1="36" x2="42" y2="36" :stroke="barColor" stroke-width="1.2" />
    <line x1="22" y1="39" x2="42" y2="39" :stroke="barColor" stroke-width="1.2" />
    <!-- Grille center divider -->
    <line x1="32" y1="30" x2="32" y2="42" :stroke="barColor" stroke-width="1.2" />
    <!-- Left headlight -->
    <ellipse cx="14" cy="34" rx="4" ry="3.5" :fill="headlightColor">
      <animate
        v-if="animate"
        attributeName="opacity"
        values="0.7;1;0.7"
        dur="2s"
        repeatCount="indefinite"
      />
    </ellipse>
    <ellipse cx="14" cy="34" rx="2" ry="2" fill="white" opacity="0.9" />
    <!-- Right headlight -->
    <ellipse cx="50" cy="34" rx="4" ry="3.5" :fill="headlightColor">
      <animate
        v-if="animate"
        attributeName="opacity"
        values="0.7;1;0.7"
        dur="2s"
        repeatCount="indefinite"
      />
    </ellipse>
    <ellipse cx="50" cy="34" rx="2" ry="2" fill="white" opacity="0.9" />
    <!-- Hood line -->
    <path
      d="M20 20 C24 18 40 18 44 20"
      stroke="currentColor"
      stroke-width="1"
      opacity="0.3"
      fill="none"
    />
  </svg>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  size?: number
  className?: string
  animate?: boolean
  bodyColor?: string
  grillColor?: string
  barColor?: string
  headlightColor?: string
}>(), {
  size: 32,
  className: '',
  animate: false,
  bodyColor: '#6b7280',
  grillColor: '#1f2937',
  barColor: '#9ca3af',
  headlightColor: '#fbbf24',
})
</script>
