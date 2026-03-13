<script setup lang="ts">
import type { Agent } from '@/services/api'

const { agent, desaturated = false, showSharedStatus = false } = defineProps<{
    agent: Agent
    desaturated?: boolean,
    showSharedStatus?: boolean
    size?: 'normal' | 'large' | undefined
  }>()
</script>

<template>
  <div class="flex rounded-full overflow-hidden" :class="{ 'grayscale': desaturated }">
    <Avatar :class="agent.icon ? '!bg-[#F4F4F4]' : desaturated ? '!bg-auxiliar-gray dark:!bg-abstracta' : '!bg-abstracta-lighter'" shape="circle" :size="size">
      <template #icon>
        <IconSparkles :size="size === 'large' ? '32' : '24'" v-if="!agent.icon" fill="currentColor" :color="desaturated ? 'var(--color-white)' : 'var(--color-abstracta)'"/>
        <img v-else :src="`data:image/png;base64,${agent.icon}`"/>
      </template>
    </Avatar>
  </div>
  <IconLock v-if="showSharedStatus && !agent.team" class="absolute -bottom-1 -right-1 bg-surface-muted rounded-full p-0.5 border-[.1px] !w-4 !h-4" />
</template>
