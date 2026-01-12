<script lang="ts" setup>
const props = defineProps<{ show: boolean, title: string, buttonText?: string }>()
const emit = defineEmits(['save', 'close'])

const onClose = () => {
  //This avoids double submit when double click in button
  if (!props.show) {
    return
  }
  emit('close')
}

const onSave = () => {
  //This avoids double submit when double click in button
  if (!props.show) {
    return
  }
  emit('save')
}
</script>

<template>
  <Modal :show="show" :title="title" @close="onClose" class="group">
    <div class="flex flex-col gap-2 my-1 modal-form *:flex *:flex-col">
      <slot/>
    </div>
    <SimpleButton @click="onSave" shape="square" size="small" class="w-full" variant="primary" >
      <span>{{ buttonText }}</span>
    </SimpleButton>
  </Modal>
</template>

<style>

.modal-form label {
  font-weight: bold;
}

.modal-form textarea,
.modal-form input {
  resize: none;
  outline-color: var(--color-auxiliar-gray);
  border: var(--border);
  border-radius: var(--spacing);
}

.modal-form .warning {
  color: var(--color-warn);
  outline-color: var(--color-warn);
}

.modal-form .error {
  color: var(--color-error);
  outline-color: var(--color-error);
}
</style>