<script setup lang="ts">
const { size = 'full', padding = 'medium'} = defineProps<{
    size?: 'fixed' | 'full'
    padding?: 'small' | 'medium'
}>();

const stickyClasses = `flex justify-center sticky bottom-0 left-0 right-0 ${padding === 'small' ? 'py-2' : 'py-4' }`

</script>

<template>
    <!-- Used for full containers like discover -->
    <div v-if="size === 'full'" class="bg-gradient-to-t from-surface/80 via-surface/80 to-transparent h-24" :class="stickyClasses">
        <slot/>
    </div>
    <!-- Used for fixed containers like cards, don't forget to add a shadow="gradient" to the button inside the slot -->
    <div v-else :class="stickyClasses">
        <slot/>
    </div>
</template>