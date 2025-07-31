<template>
  <div
    class="flex min-h-[calc(100vh-90px)] flex-col items-center justify-center"
  >
    <div class="w-full max-w-md">
      <NuxtPage />

      <!-- Footer -->
      <footer class="mt-2 w-full px-8 py-4">
        <div
          class="container mx-auto flex flex-col items-center justify-center space-y-2 text-sm text-gray-400 md:flex-row md:justify-between md:space-y-0"
        >
          <div class="flex space-x-4">© 2025 JEP. All rights reserved.</div>
          <div>
            <NuxtLink
              href="/legal/impress"
              class="transition-colors hover:text-black"
            >
              Impressum
            </NuxtLink>
            |

            <NuxtLink
              href="/legal/data-protection"
              class="transition-colors hover:text-black"
            >
              Datenschutz
            </NuxtLink>
          </div>
        </div>
      </footer>
    </div>
  </div>
</template>
<script lang="ts" setup>
  // TODO: add nuxt/nitro variables to linter
  provideHeadlessUseId(() => useId()) // eslint-disable-line no-undef
</script>
