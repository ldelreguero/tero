<script lang="ts" setup>
defineProps<{
  isCollapsed: boolean;
}>();
</script>

<template>
  <FlexCard :class="[isCollapsed ? '!w-20 px-2' : 'w-full !w-sm px-3']">
    <template #header>
      <div class="flex items-center" :class="isCollapsed ? 'flex-col' : 'justify-between'">
        <div class="w-8 h-8 rounded-full bg-auxiliar-gray animate-pulse"></div>
        <div v-if="!isCollapsed" class="flex items-center gap-2">
          <div class="w-24 h-8 rounded-full bg-auxiliar-gray animate-pulse"></div>
          <div class="w-8 h-8 rounded-full bg-auxiliar-gray animate-pulse"></div>
        </div>
      </div>
    </template>
    <div class="flex-1">
      <div class="flex items-center gap-3 p-2">
        <div class="w-8 h-8 rounded-full bg-auxiliar-gray animate-pulse"></div>
        <div v-if="!isCollapsed" class="flex-1">
          <div class="h-5 bg-auxiliar-gray rounded animate-pulse w-3/4"></div>
        </div>
      </div>
      <div v-for="n in 3" :key="n" class="flex items-center gap-3 p-2">
        <div class="w-8 h-8 rounded-full bg-auxiliar-gray animate-pulse"></div>
        <div v-if="!isCollapsed" class="flex-1">
          <div class="h-5 bg-auxiliar-gray rounded animate-pulse w-3/4"></div>
        </div>
      </div>
      <div v-if="!isCollapsed" class="mt-5">
        <div class="sticky top-0 bg-surface z-10">
          <div class="flex justify-between items-center">
            <div class="h-6 bg-auxiliar-gray rounded animate-pulse w-24"></div>
          </div>
        </div>

        <div v-for="n in 3" :key="n" class="flex items-center gap-3 p-2">
          <div class="w-8 h-8 rounded-full bg-auxiliar-gray animate-pulse"></div>
          <div class="flex-1">
            <div class="h-5 bg-auxiliar-gray rounded animate-pulse w-3/4"></div>
          </div>
        </div>
      </div>
    </div>
    <div class="mt-auto py-6 border-t border-auxiliar-gray">
      <div v-if="!isCollapsed" class="mb-4">
        <div class="h-[12px] bg-auxiliar-gray rounded-full animate-pulse"></div>
      </div>
      <div :class="isCollapsed ? 'flex justify-center' : ''">
        <div class="w-full">
          <div class="h-10 bg-auxiliar-gray rounded-full animate-pulse px-4"></div>
        </div>
      </div>
    </div>
  </FlexCard>
</template>
