<script lang="ts">
export class ErrorMessage {
  title: string
  message: string

  constructor(title: string, message: string) {
    this.title = title
    this.message = message
  }
}
</script>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { AnimationEffect } from '../../utils/animations'
import { IconX, IconAlertTriangle } from '@tabler/icons-vue'


const props = defineProps<{
  error?: ErrorMessage
}>()

const showError = ref(props.error !== undefined)
const errorBoxRef = ref<HTMLElement | null>(null)

const close = () => {
  showError.value = false
}

watch(
  () => props.error,
  async (newVal) => {
    const wasHidden = !showError.value
    showError.value = !!newVal?.title
    // Smooth scroll to error box when it appears, useful when you have a lot of content above the error box
    if (wasHidden && showError.value) {
      await nextTick()
      setTimeout(() => {
        errorBoxRef.value?.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }, 100)
    }
  }
)
</script>

<template>
  <Animate :effect="AnimationEffect.QUICK_SLIDE_UP" v-if="showError && error?.title && error?.message">
    <div ref="errorBoxRef" class="flex items-center px-3 py-2 my-3 border border-error-alt rounded-2xl whitespace-pre-line relative bg-surface shadow-md">
      <button @click="close" class="absolute top-2 right-2">
        <IconX class="w-5 h-5 hover:text-error-alt" />
      </button>
      <div>
        <div class="font-medium flex items-center">
          <IconAlertTriangle class="text-error-alt flex-shrink-0 mr-2 h-7 w-7" />
          {{ error.title }}
        </div>
        <div class="py-2 text-light-gray">{{ error.message }}</div>
      </div>
    </div>
  </Animate>
</template>
