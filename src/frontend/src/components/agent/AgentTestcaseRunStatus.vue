<script setup lang="ts">
import { IconSquareCheckFilled, IconSquareXFilled, IconExclamationMark, IconSquareChevronsRightFilled } from '@tabler/icons-vue'

defineProps<{
  passed: number
  failed: number
  error: number
  skipped: number
}>()
</script>

<template>
  <div class="flex flex-row items-center gap-1">
    <div class="flex flex-row items-center gap-2 min-w-14">
      <IconSquareCheckFilled class="text-success" />
      <span>{{ passed }}</span>
    </div>
    <div class="flex flex-row items-center gap-2 min-w-14">
      <IconSquareXFilled class="text-error" />
      <span>{{ failed }}</span>
    </div>
    <div class="flex flex-row items-center gap-2 min-w-14">
      <IconExclamationMark class="text-white bg-warn rounded-sm p-0.5" size="20"/>
      <span>{{ error }}</span>
    </div>
    <div class="flex flex-row items-center gap-2 min-w-14">
      <IconSquareChevronsRightFilled class="text-light-gray" />
      <span>{{ skipped }}</span>
    </div>
  </div>
</template>
