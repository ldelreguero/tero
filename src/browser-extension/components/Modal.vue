<script lang="ts" setup>
import { IconX } from '@tabler/icons-vue'

defineProps<{ show: boolean, title: string, icon?: string }>()
</script>

<template>
  <Transition name="modal">
    <div v-if="show"
      class="flex absolute z-auto top-0 left-0 w-full h-full bg-content/20 transition-opacity duration-300 ease-in-out rounded-tl-3xl rounded-bl-3xl">
      <div
        class="w-80 h-auto m-auto p-3 bg-surface rounded-xl shadow-md transition-all duration-300 ease-in-out">
        <div class="modal-header flex flex-row">
          <img :src="icon" v-if="icon" />
          <h2 class="font-medium !text-current self-center !text-xl">{{ title }}</h2>
          <div class="modal-actions flex flex-auto flex-row-reverse">
            <button @click="$emit('close')"><IconX /></button>
          </div>
        </div>
        <slot />
      </div>
    </div>
  </Transition>
</template>

<style>
.modal-enter-from {
  opacity: 0;
}

.modal-leave-to {
  opacity: 0;
}
</style>