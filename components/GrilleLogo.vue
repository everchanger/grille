<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 64 64"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    :class="className"
  >
    <!-- Minimal body frame — just a thin band around the front fascia -->
    <path
      d="M4 28 C4 24 8 20 14 20 L50 20 C56 20 60 24 60 28 L60 48 C60 50 58 52 56 52 L8 52 C6 52 4 50 4 48 Z"
      :fill="bodyColor"
    />
    <!-- Left headlight (large, prominent) -->
    <ellipse cx="11" cy="36" rx="6" ry="8" :fill="headlightColor">
      <animate
        v-if="animate"
        attributeName="opacity"
        values="0.7;1;0.7"
        dur="2s"
        repeatCount="indefinite"
      />
    </ellipse>
    <ellipse cx="11" cy="34" rx="3" ry="3" fill="white" opacity="0.85" />
    <!-- Right headlight (large, prominent) -->
    <ellipse cx="53" cy="36" rx="6" ry="8" :fill="headlightColor">
      <animate
        v-if="animate"
        attributeName="opacity"
        values="0.7;1;0.7"
        dur="2s"
        repeatCount="indefinite"
      />
    </ellipse>
    <ellipse cx="53" cy="34" rx="3" ry="3" fill="white" opacity="0.85" />
    <!-- Grille (large, central focus) -->
    <rect x="18" y="24" width="28" height="24" rx="3" :fill="grillColor" />
    <!-- Grille horizontal bars (5 bars for more detail) -->
    <line x1="18" y1="28" x2="46" y2="28" :stroke="barColor" stroke-width="1.4" />
    <line x1="18" y1="32" x2="46" y2="32" :stroke="barColor" stroke-width="1.4" />
    <line x1="18" y1="36" x2="46" y2="36" :stroke="barColor" stroke-width="1.4" />
    <line x1="18" y1="40" x2="46" y2="40" :stroke="barColor" stroke-width="1.4" />
    <line x1="18" y1="44" x2="46" y2="44" :stroke="barColor" stroke-width="1.4" />
    <!-- Grille center divider -->
    <line x1="32" y1="24" x2="32" y2="48" :stroke="barColor" stroke-width="1.4" />
    <!-- Subtle hood edge -->
    <line x1="14" y1="21" x2="50" y2="21" :stroke="bodyColor" stroke-width="1.5" opacity="0.4" />
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
