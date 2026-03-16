<script setup lang="ts">
const props = defineProps<{
  count?: number;
}>();

const SKELETON_COUNT = props.count || 9;
</script>

<template>
  <template v-for="i in SKELETON_COUNT" :key="i">
    <div class="grid-card bg-surface-muted px-3 py-2.5 animate-pulse">
      <div class="h-4 bg-auxiliar-gray rounded w-3/4 mb-2"></div>
      <div class="h-3 bg-auxiliar-gray rounded w-1/2 mb-4"></div>
      <div class="mt-auto flex justify-between items-center">
        <div class="h-4 bg-auxiliar-gray rounded w-20"></div>
        <div class="h-5 w-5 bg-auxiliar-gray rounded-full"></div>
      </div>
    </div>
  </template>
</template>
