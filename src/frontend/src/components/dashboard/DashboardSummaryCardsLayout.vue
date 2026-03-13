<script setup lang="ts">

const props = defineProps<{
    loading: boolean;
    numberOfCards: number;
}>();

</script>

<template>
    <div class="flex w-full gap-4">
        <div v-if="props.loading" class="w-full">
            <div class="flex w-full gap-4">
                <div v-for="i in props.numberOfCards" :key="i" 
                     :class="[
                         props.numberOfCards === 1 ? 'w-full' : 
                         props.numberOfCards === 2 ? 'w-1/2' : 
                         props.numberOfCards === 3 ? 'w-1/3' : 'w-1/4',
                         'bg-surface-muted rounded-lg p-4 animate-pulse'
                     ]">
                    <div class="flex items-center justify-between gap-2 mb-2">
                        <div class="h-4 bg-auxiliar-gray rounded w-24"></div>
                        <div class="h-8 w-8 bg-auxiliar-gray rounded-full"></div>
                    </div>
                    <div class="h-10 bg-auxiliar-gray rounded w-20 mt-2"></div>
                </div>
            </div>
        </div>
        <div v-else class="flex w-full gap-4">
            <slot></slot>
        </div>
    </div>
</template>
