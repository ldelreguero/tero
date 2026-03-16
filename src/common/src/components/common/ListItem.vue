<script lang="ts" setup>
const emit = defineEmits<{
  (e: 'click', event: MouseEvent): void
}>()
</script>

<template>
    <div class="flex gap-2 items-center p-3 py-1 hover:bg-surface-muted/50 rounded-lg cursor-pointer min-h-[48px]"
        @click="emit('click', $event)">
        <slot name="start"></slot>
        <div class="flex-grow truncate">
            <slot></slot>
        </div>
        <slot name="end"></slot>
    </div>
</template>