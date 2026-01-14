<script setup lang="ts">
import { AutomaticAgentField } from '@/services/api'
import { Dialog } from 'primevue'
import { useI18n } from 'vue-i18n'
import { computed } from 'vue'

const visible = defineModel<boolean>("visible")
const props = defineProps<{
  field?: AutomaticAgentField
}>()
const emit = defineEmits<{
  (e: 'generate'): void
}>()

const { t } = useI18n()

const disclaimer = computed(() => {
  return t('generateAgentDisclaimer', { field: t(`generateAgentField${props.field}`) })
})
</script>

<template>
  <Dialog v-model:visible="visible" :modal="true" :draggable="false" :resizable="false" :closable="false" class="basic-dialog">
    <div class="flex flex-col gap-4 bg-white rounded-xl p-4 pt-6"> 
      <span v-html="disclaimer" class="w-full whitespace-pre-line"></span>
      <div class="flex flex-row gap-2 items-center justify-end">
        <SimpleButton @click="visible = false" shape="square">{{ t('cancel') }}</SimpleButton>
        <SimpleButton @click="emit('generate')" variant="primary" shape="square">{{ t('confirmButton') }}</SimpleButton>
      </div>
    </div>
  </Dialog>
</template>


<i18n lang="json">
{
  "en": {
    "confirmButton": "Confirm",
    "cancel": "Cancel",
    "generateAgentTitle": "Generate",
    "generateAgentFieldNAME": "name",
    "generateAgentFieldDESCRIPTION": "description",
    "generateAgentFieldSYSTEM_PROMPT": "instructions",
    "generateAgentDisclaimer": "{'<'}b>Attention!{'<'}/b> \n\n This action will automatically generate a value for the {'<'}b>{field}{'<'}/b> field and replace the current value.\n\n{'<'}b>This action cannot be undone.{'<'}/b>"
  },
  "es": {
    "confirmButton": "Confirmar",
    "cancel": "Cancelar",
    "generateAgentFieldNAME": "nombre",
    "generateAgentFieldDESCRIPTION": "descripción",
    "generateAgentFieldSYSTEM_PROMPT": "instrucciones",
    "generateAgentDisclaimer": "{'<'}b>¡Atención!{'<'}/b> \n\n Esta acción generará automáticamente un valor para el campo {'<'}b>{field}{'<'}/b> y reemplazará el valor actual.\n\n{'<'}b>Esta acción no se puede deshacer.{'<'}/b>"
  }
}
</i18n>