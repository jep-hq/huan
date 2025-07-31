import { defineNuxtConfig } from 'nuxt/config'
import tailwindcss from '@tailwindcss/vite'

export default defineNuxtConfig({
  future: {
    compatibilityVersion: 4,
  },

  modules: ['nuxt-headlessui', '@nuxtjs/seo', 'shadcn-nuxt'],

  site: {
    // set site by environment variables
    url: process.env.VITE_APP_SITE_URL,
    name: process.env.VITE_APP_SITE_NAME,
    description: process.env.VITE_APP_SITE_DESCRIPTION,
  },

  ssr: true,
  devtools: { enabled: true },
  nitro: {
    preset: 'aws-lambda',
  },

  build: {
    transpile: ['@heroicons/vue'],
  },
  css: ['~/assets/css/main.css'],

  //security: {
  //  headers: {},
  //},

  shadcn: {
    /**
     * Prefix for all the imported component
     */
    prefix: '',
    /**
     * Directory that the component lives in.
     * @default "./components/ui"
     */
    componentDir: './app/components/ui',
  },

  vite: {
    plugins: [tailwindcss()],
    build: {
      sourcemap: true,
    },
    css: {
      devSourcemap: true,
    },
    optimizeDeps: {
      include: ['jsdoc-type-pratt-parser'],
    },
  },
  compatibilityDate: '2024-08-12',
})
