<script setup lang="ts">

defineProps<{
    title: string;
    compactDisplay?: boolean;
}>();

</script>

<template>
    <div class="flex flex-col border-1 border-auxiliar-gray h-full relative" :class="{ 'border-none p-0': compactDisplay, 'p-4 gap-2 pt-0 rounded-xl': !compactDisplay }">
        <div class="flex justify-between items-center sticky top-0 bg-surface z-10 pt-4 pb-2" :class="{ 'py-2 pr-1': compactDisplay }">
            <span class="font-medium" :class="{ 'text-md': compactDisplay, 'text-lg': !compactDisplay }">{{ title }}</span>
            <slot name="actions" ></slot>
        </div>
        <div class="flex-1 overflow-y-auto">
            <slot></slot>
            <GradientBottom size="fixed" >
                <slot name="footer"></slot>
            </GradientBottom>
        </div>
    </div>
</template>