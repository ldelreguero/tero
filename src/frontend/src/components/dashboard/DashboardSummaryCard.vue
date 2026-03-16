<script setup lang="ts">
defineProps<{
    title: string;
    icon: string;
}>();
</script>

<template>
    <div class="flex flex-col border-1 rounded-xl p-4">
        <div class="flex items-center justify-between gap-2">
            <span class="text-lg font-medium">{{ title }}</span>
            <div class="flex items-center justify-center bg-primary text-white dark:bg-surface-muted dark:text-primary rounded-full p-1">
                <component :is="icon" size="24" />
            </div>
        </div>
        <div class="flex flex-col gap-2">
            <span class="text-5xl font-medium truncate">
                <slot name="value" />
            </span>
            <span class="flex items-center gap-2 text-sm font-medium">
                <slot name="previousMonthComparison" />
            </span>
        </div>
    </div>
</template>