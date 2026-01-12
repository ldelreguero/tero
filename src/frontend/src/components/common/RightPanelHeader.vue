<script setup lang="ts">
defineProps<{
  title?: string;
  icon?: string;
  invitationAccepted?: boolean;
}>();

const emit = defineEmits<{
    (e: 'invitationAccepted'): void
}>();
</script>

<template>
  <div class="w-full h-[74px] bg-[url('@/assets/images/banner.webp')] bg-cover bg-center bg-blend-overlay dark:bg-surface/70 rounded-t-lg shadow-md flex justify-between lg:grid grid-cols-3 items-center px-8 py-2">
    <div>
      <Logo />
    </div>
    <div class="flex justify-center">
      <slot name="center" />
    </div>
    <div class="flex items-center gap-4 justify-end">
      <div class="flex items-center gap-2" v-if="title">
        <component :is="icon" class="text-white" />
        <h1 class="text-white text-2xl font-medium">{{ title }}</h1>
      </div>
      <Notifications
        @invitation-accepted="invitationAccepted ? emit('invitationAccepted') : undefined"
      />
    </div>
  </div>
</template>
