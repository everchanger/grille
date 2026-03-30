<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="open"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
        @click.self="dismiss"
      >
        <div class="bg-gray-900/90 backdrop-blur-xl rounded-2xl p-6 w-full max-w-sm mx-4 border border-white/10 ring-1 ring-white/5 shadow-2xl shadow-black/40 animate-scale-in max-h-[85vh] overflow-y-auto">
          <div class="flex justify-between items-center mb-4">
            <h2 class="text-white font-extrabold text-lg">
              How to Play
            </h2>
            <button
              class="text-gray-500 hover:text-white text-xl transition-colors duration-200"
              @click="dismiss"
            >
              ✕
            </button>
          </div>

          <p class="text-gray-300 text-sm mb-4">
            Guess the iconic car in <span class="text-white font-bold">5 tries</span>. Each guess reveals clues about the mystery car.
          </p>

          <h3 class="text-gray-500 text-[10px] font-bold uppercase tracking-wider mb-3">Feedback Guide</h3>

          <div class="space-y-2 mb-5">
            <div class="flex items-center gap-3 px-3 py-2 rounded-lg bg-gradient-to-r from-emerald-600/20 to-green-700/10 border border-emerald-500/20">
              <span class="text-lg">✅</span>
              <div>
                <span class="text-white text-sm font-semibold">Green</span>
                <span class="text-gray-400 text-xs block">Correct — exact match</span>
              </div>
            </div>
            <div class="flex items-center gap-3 px-3 py-2 rounded-lg bg-gradient-to-r from-amber-500/20 to-yellow-600/10 border border-amber-500/20">
              <span class="text-lg">🟡</span>
              <div>
                <span class="text-white text-sm font-semibold">Yellow Circle</span>
                <span class="text-gray-400 text-xs block">Close — same region or origin</span>
              </div>
            </div>
            <div class="flex items-center gap-3 px-3 py-2 rounded-lg bg-gradient-to-r from-amber-500/20 to-yellow-600/10 border border-amber-500/20">
              <span class="text-lg">🔼🔽</span>
              <div>
                <span class="text-white text-sm font-semibold">Yellow Arrow</span>
                <span class="text-gray-400 text-xs block">Close — almost there, arrow shows direction</span>
              </div>
            </div>
            <div class="flex items-center gap-3 px-3 py-2 rounded-lg bg-white/[0.04] border border-white/10">
              <span class="text-lg">🔼</span>
              <div>
                <span class="text-white text-sm font-semibold">Arrow Up</span>
                <span class="text-gray-400 text-xs block">The answer is higher</span>
              </div>
            </div>
            <div class="flex items-center gap-3 px-3 py-2 rounded-lg bg-white/[0.04] border border-white/10">
              <span class="text-lg">🔽</span>
              <div>
                <span class="text-white text-sm font-semibold">Arrow Down</span>
                <span class="text-gray-400 text-xs block">The answer is lower</span>
              </div>
            </div>
            <div class="flex items-center gap-3 px-3 py-2 rounded-lg bg-red-600/10 border border-red-500/20">
              <span class="text-lg">❌</span>
              <div>
                <span class="text-white text-sm font-semibold">Red</span>
                <span class="text-gray-400 text-xs block">Wrong — no match</span>
              </div>
            </div>
          </div>

          <div class="px-3 py-2.5 rounded-lg bg-white/[0.03] border border-white/5 mb-5">
            <p class="text-gray-400 text-xs leading-relaxed">
              🖼️ <span class="text-gray-300">The car image gets clearer with each guess.</span> Start with a silhouette, progress to a blurred photo, and finally see the full reveal!
            </p>
          </div>

          <button
            class="w-full py-2.5 bg-white hover:bg-gray-200 text-gray-900 rounded-xl font-semibold text-sm shadow-lg shadow-black/20 transition-all duration-200"
            @click="dismiss"
          >
            Got it!
          </button>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
const props = defineProps<{
  open: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const dismiss = () => {
  if (import.meta.client) {
    localStorage.setItem('grille_instructions_seen', 'true')
  }
  emit('close')
}
</script>

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
