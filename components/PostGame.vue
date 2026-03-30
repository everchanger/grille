<template>
  <Teleport to="body">
    <Transition name="postgame">
      <div
        v-if="open"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
        @click.self="$emit('close')"
      >
        <!-- Confetti canvas (only on win) -->
        <canvas
          v-if="solved"
          ref="confettiCanvas"
          class="fixed inset-0 pointer-events-none z-[60]"
        />

        <div class="bg-gray-900/90 backdrop-blur-xl rounded-2xl p-6 w-full max-w-sm mx-4 border border-white/10 ring-1 ring-indigo-500/10 shadow-2xl shadow-black/40 animate-scale-in max-h-[85vh] overflow-y-auto">
          <div class="flex justify-end mb-2">
            <button class="text-gray-500 hover:text-white text-xl transition-colors duration-200" @click="$emit('close')">✕</button>
          </div>

          <div class="text-center mb-4">
            <p v-if="solved" class="text-emerald-400 font-bold text-lg animate-slide-in">🎉 You got it!</p>
            <p v-else class="text-red-400 font-bold text-lg animate-slide-in">The answer was...</p>
            <h2 class="text-white text-2xl font-extrabold mt-1 bg-gradient-to-r from-white to-indigo-200 bg-clip-text text-transparent">
              {{ car.make }} {{ car.model }}
            </h2>
            <p class="text-indigo-300/60 text-sm mt-0.5">{{ car.year }} · {{ car.country }}</p>
          </div>

          <img
            :src="resolvedImage"
            :alt="`${car.make} ${car.model}`"
            class="w-full max-w-sm mx-auto rounded-xl mb-4 object-cover h-48 ring-1 ring-white/10"
          />

          <div class="grid grid-cols-2 gap-2 text-sm mb-4">
            <div class="bg-white/[0.05] rounded-lg p-2.5 border border-white/5">
              <span class="text-indigo-400/70 block text-xs">Engine</span>
              <span class="text-white font-semibold">{{ car.engine }}</span>
            </div>
            <div class="bg-white/[0.05] rounded-lg p-2.5 border border-white/5">
              <span class="text-indigo-400/70 block text-xs">Drivetrain</span>
              <span class="text-white font-semibold">{{ car.drivetrain }}</span>
            </div>
            <div class="bg-white/[0.05] rounded-lg p-2.5 border border-white/5">
              <span class="text-indigo-400/70 block text-xs">Horsepower</span>
              <span class="text-white font-semibold">{{ car.horsepower }} hp</span>
            </div>
            <div class="bg-white/[0.05] rounded-lg p-2.5 border border-white/5">
              <span class="text-indigo-400/70 block text-xs">Weight</span>
              <span class="text-white font-semibold">{{ formatWeight(car.weight_kg) }}</span>
            </div>
          </div>

          <p class="text-gray-400 text-sm italic mb-4">{{ car.fact }}</p>

          <div class="flex flex-col gap-2">
            <a
              :href="car.wiki"
              target="_blank"
              rel="noopener noreferrer"
              class="text-indigo-400 text-sm text-center hover:text-indigo-300 transition-colors duration-200"
            >
              Read more ↗
            </a>
            <button
              class="w-full py-2.5 bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 text-white rounded-xl font-semibold text-sm shadow-lg shadow-indigo-500/20 transition-all duration-200 hover:shadow-indigo-500/30"
              @click="$emit('share')"
            >
              📋 Share Result
            </button>
          </div>

          <div class="mt-4 text-center text-gray-500 text-xs">
            <p>Next puzzle in <span class="text-indigo-300 font-semibold">{{ countdown }}</span></p>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.postgame-enter-active,
.postgame-leave-active {
  transition: opacity 0.3s ease;
}
.postgame-enter-active > div:not(canvas),
.postgame-leave-active > div:not(canvas) {
  transition: transform 0.3s ease, opacity 0.3s ease;
}
.postgame-enter-from,
.postgame-leave-to {
  opacity: 0;
}
.postgame-enter-from > div:not(canvas),
.postgame-leave-to > div:not(canvas) {
  transform: scale(0.9) translateY(20px);
  opacity: 0;
}
</style>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import type { Car } from '~/types'
import { useUnits } from '~/composables/useUnits'
import { resolveAssetUrl } from '~/utils/useAssetUrl'

const props = defineProps<{
  open: boolean
  car: Car
  solved: boolean
}>()

defineEmits<{
  (e: 'share'): void
  (e: 'close'): void
}>()

const { formatWeight } = useUnits()
const resolvedImage = computed(() => resolveAssetUrl(props.car.image))
const countdown = ref('')
const confettiCanvas = ref<HTMLCanvasElement | null>(null)

const updateCountdown = () => {
  const now = new Date()
  const tomorrow = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() + 1))
  const diff = tomorrow.getTime() - now.getTime()
  const h = Math.floor(diff / 3600000)
  const m = Math.floor((diff % 3600000) / 60000)
  const s = Math.floor((diff % 60000) / 1000)
  countdown.value = `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

let timer: ReturnType<typeof setInterval>
let confettiCleanupTimer: ReturnType<typeof setTimeout>
let confettiLaunchTimer: ReturnType<typeof setTimeout>
let confettiAnimId: number

onMounted(() => {
  updateCountdown()
  timer = setInterval(updateCountdown, 1000)
})
onUnmounted(() => {
  clearInterval(timer)
  clearTimeout(confettiCleanupTimer)
  clearTimeout(confettiLaunchTimer)
  cancelAnimationFrame(confettiAnimId)
})

// Confetti effect
interface Particle {
  x: number
  y: number
  vx: number
  vy: number
  size: number
  color: string
  rotation: number
  rotationSpeed: number
  opacity: number
}

const launchConfetti = () => {
  const canvas = confettiCanvas.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  canvas.width = window.innerWidth
  canvas.height = window.innerHeight

  const colors = ['#6366f1', '#818cf8', '#34d399', '#fbbf24', '#f87171', '#a78bfa', '#38bdf8', '#fb923c']
  const particles: Particle[] = []

  for (let i = 0; i < 100; i++) {
    particles.push({
      x: canvas.width / 2 + (Math.random() - 0.5) * 200,
      y: canvas.height * 0.4,
      vx: (Math.random() - 0.5) * 15,
      vy: -Math.random() * 18 - 5,
      size: Math.random() * 8 + 4,
      color: colors[Math.floor(Math.random() * colors.length)],
      rotation: Math.random() * 360,
      rotationSpeed: (Math.random() - 0.5) * 10,
      opacity: 1,
    })
  }

  let animId: number
  const gravity = 0.4
  const drag = 0.99

  const animate = () => {
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    let alive = false

    for (const p of particles) {
      p.vy += gravity
      p.vx *= drag
      p.x += p.vx
      p.y += p.vy
      p.rotation += p.rotationSpeed
      p.opacity -= 0.005

      if (p.opacity <= 0) continue
      alive = true

      ctx.save()
      ctx.globalAlpha = p.opacity
      ctx.translate(p.x, p.y)
      ctx.rotate((p.rotation * Math.PI) / 180)
      ctx.fillStyle = p.color
      ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size * 0.6)
      ctx.restore()
    }

    if (alive) {
      animId = requestAnimationFrame(animate)
    } else {
      ctx.clearRect(0, 0, canvas.width, canvas.height)
    }
  }

  animId = requestAnimationFrame(animate)
  confettiAnimId = animId

  confettiCleanupTimer = setTimeout(() => {
    cancelAnimationFrame(animId)
    if (ctx) ctx.clearRect(0, 0, canvas.width, canvas.height)
  }, 5000)
}

watch(() => props.open, async (isOpen) => {
  if (isOpen && props.solved) {
    await nextTick()
    confettiLaunchTimer = setTimeout(launchConfetti, 300)
  }
})
</script>
