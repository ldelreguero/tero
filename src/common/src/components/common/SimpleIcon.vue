<script setup lang="ts">
import type { Icon } from '@tabler/icons-vue'

defineProps<{
  icon: Icon
  size?: number
  class?: string
  interactive?: boolean
  filled?: boolean
}>()

const emit = defineEmits<{
  (e: 'click', event: MouseEvent): void
}>()
</script>

<template>
  <div
    :class="['flex items-center justify-center', $props.class, interactive ? 'text-content hover:text-abstracta cursor-pointer' : '']"
    @click="interactive ? emit('click', $event) : undefined"
  >
    <span v-if="filled" class="relative inline-flex items-center justify-center">
      <span class="absolute w-3.5 h-3.5 dark:bg-white rounded-[3px]"></span>
      <component :is="icon" class="relative" :size="size" />
    </span>
    <component v-else :is="icon" :size="size" />
  </div>
</template>
