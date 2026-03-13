<script lang="ts" setup>
defineProps<{
  shared: boolean
}>()
</script>

<template>
  <IconLock v-if="!shared" class="text-content-muted !w-5" />
</template>
