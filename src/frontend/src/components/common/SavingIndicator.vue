<script setup lang="ts">
import { IconDeviceFloppy } from '@tabler/icons-vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

defineProps<{
  textClass?: string
}>()
</script>

<template>
  <div class="flex flex-row px-2 items-center text-sm animate-pulse gap-2">
    <IconDeviceFloppy />
    <span :class="textClass">{{ t('saving') }}</span>
  </div>
</template>

<i18n lang="json">
{
  "en": {
    "saving": "Saving..."
  },
  "es": {
    "saving": "Guardando..."
  }
}
</i18n>
