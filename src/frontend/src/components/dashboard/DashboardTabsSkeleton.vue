<script lang="ts" setup>

const props = defineProps<{
  tabsLength: number
}>()

</script>
<template>
  <div class="flex items-center w-full border-b-1 border-auxiliar-gray pb-2 min-h-[51px] gap-6">
    <div v-for="n in props.tabsLength" :key="n" class="flex items-center gap-2">
      <div class="w-5 h-5 bg-auxiliar-gray rounded animate-pulse"></div>
      <div class="w-16 h-4 bg-auxiliar-gray rounded animate-pulse"></div>
    </div>
  </div>
</template>

