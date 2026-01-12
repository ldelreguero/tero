<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { onMounted, ref } from 'vue';

const { t } = useI18n()

const props = defineProps<{
  onSave: (value:string) => void
  onCancel: () => void
  value: string
}>()

const inputValue = ref<string>(props.value)
const inputRef = ref<HTMLInputElement | null>(null);

onMounted(()=>{
  inputRef.value?.focus();
})

</script>
<template>
  <div class="bg-surface rounded-xl shadow-md px-2 py-2 my-2 border border-auxiliar-gray">
    <div class="flex items-center justify-between gap-2">
      <Form class="flex w-full" @submit="onSave(inputValue)">
        <input
          ref="inputRef"
          @keydown.esc.prevent="props.onCancel()"
          v-model="inputValue"
          maxlength="80"
          required="true"
          class="w-full px-1 border-none active:border-none focus:border-none focus:outline-none"
          :placeholder="t('chatNamePlaceholder')"/>
        <div class="flex gap-2">
          <SimpleButton variant="secondary" size="small" @click="onCancel">
            <IconX/>
          </SimpleButton>
          <SimpleButton variant="primary" size="small" type="submit">
            <IconCheck/>
          </SimpleButton>
      </div>
    </Form>
    </div>
  </div>
</template>

<i18n>
  {
    "en": {
      "chatNamePlaceholder": "Enter chat name",
    },
    "es": {
      "chatNamePlaceholder": "Ingrese el nombre del chat",
    }
  }
</i18n>
