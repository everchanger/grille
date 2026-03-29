import { defineConfig } from 'vitest/config'
import { resolve } from 'path'

export default defineConfig({
  resolve: {
    alias: {
      '~': resolve(__dirname, '.'),
      '#imports': resolve(__dirname, '.nuxt/imports.d.ts'),
    },
  },
  plugins: [
    {
      name: 'nuxt-import-meta-client',
      transform(code) {
        return code.replace(/import\.meta\.client/g, 'true')
      },
    },
  ],
  test: {
    environment: 'happy-dom',
    include: ['tests/**/*.test.ts'],
  },
})
