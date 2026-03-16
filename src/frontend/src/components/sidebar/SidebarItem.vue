<script setup lang="ts">
import { ref } from 'vue'
const itemContent = ref<HTMLElement>()

const emit = defineEmits(['click', 'menu-toggle']);

defineProps<{
  variant?: 'default' | 'primary'
  isCollapsed?: boolean
}>()
</script>

<template>
    <div class="flex items-center hover:bg-surface-muted rounded-md cursor-pointer group px-2 py-1 w-full overflow-hidden"
         :class="[variant === 'primary' ? 'hover:!bg-abstracta hover:!text-white' : '', $attrs.class]"
         @click="emit('click')">
        <div class="flex-1" ref="itemContent">
            <slot />
        </div>
        <slot name="actions" />
    </div>
</template>
