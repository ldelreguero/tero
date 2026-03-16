<script setup lang="ts">
import type { ExternalAgent } from '@/services/api'
import externalAgentIcon from '@/assets/images/icon-external-agent.svg'

const { externalAgent } = defineProps<{
    externalAgent: ExternalAgent
    size?: 'normal' | 'large' | undefined
    bordered?: boolean
  }>()
</script>

<template>
  <Avatar :class="`'bg-surface' ${bordered ? 'border-1' : ''}`" shape="circle" :size="size">
    <template #icon>
      <img v-if="!externalAgent.icon" :src="externalAgentIcon" class="p-1" />
      <img v-else :src="`data:image/png;base64,${externalAgent.icon}`" />
    </template>
  </Avatar>
</template>