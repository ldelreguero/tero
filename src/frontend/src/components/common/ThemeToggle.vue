<script setup lang="ts">
import { IconMoon, IconSun } from '@tabler/icons-vue'
import { useI18n } from 'vue-i18n'
import { useTheme } from '@/composables/useTheme'

const { t } = useI18n()
const { theme, setTheme } = useTheme()
</script>

<template>
  <div class="flex items-center justify-between gap-2 px-2 sm:px-3 py-2">
    <span class="text-sm text-light-gray">{{ t('themeLabel') }}</span>

    <div class="inline-flex rounded-xl border border-auxiliar-gray overflow-hidden">
      <button
        type="button"
        class="flex items-center gap-1 px-2.5 py-1.5 text-sm"
        :class="theme === 'light' ? 'bg-abstracta text-white' : 'bg-surface text-dark-gray hover:bg-surface-muted'"
        :aria-pressed="theme === 'light'"
        @click="setTheme('light')"
      >
        <IconSun size="16" />
        <span>{{ t('light') }}</span>
      </button>

      <button
        type="button"
        class="flex items-center gap-1 px-2.5 py-1.5 text-sm border-l border-auxiliar-gray"
        :class="theme === 'dark' ? 'bg-abstracta text-white' : 'bg-surface text-dark-gray hover:bg-surface-muted'"
        :aria-pressed="theme === 'dark'"
        @click="setTheme('dark')"
      >
        <IconMoon size="16" />
        <span>{{ t('dark') }}</span>
      </button>
    </div>
  </div>
</template>

<i18n lang="json">
{
  "en": {
    "themeLabel": "Theme",
    "light": "Light",
    "dark": "Dark"
  },
  "es": {
    "themeLabel": "Tema",
    "light": "Claro",
    "dark": "Oscuro"
  }
}
</i18n>
