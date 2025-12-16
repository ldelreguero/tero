<script setup lang="ts">
const props = defineProps<{
  tooltip?: string
}>()
const emit = defineEmits<{
  (e: 'confirm'): void
  (e: 'cancel'): void
}>()
</script>

<template>
  <div class="bg-surface rounded-xl shadow-md px-2 py-2 my-2 border border-auxiliar-gray">
    <div class="flex items-center justify-between">
      <span class="text-md font-medium">{{ props.tooltip }}</span>
      <div class="flex gap-2">
        <SimpleButton variant="secondary" size="small" @click="emit('cancel')">
          <IconX/>
        </SimpleButton>
        <SimpleButton variant="error" size="small" @click.prevent="emit('confirm')">
          <IconCheck/>
        </SimpleButton>
      </div>
    </div>
  </div>
</template>
