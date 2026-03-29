export default defineNuxtConfig({
  compatibilityDate: '2024-11-01',
  devtools: { enabled: true },
  modules: ['@nuxtjs/tailwindcss'],
  ssr: false,
  nitro: {
    preset: 'github-pages',
    output: {
      publicDir: '../.output/public',
    },
  },
  app: {
    baseURL: '/grille/',
  },
})
