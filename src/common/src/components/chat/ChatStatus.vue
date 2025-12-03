<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { IconChevronDown } from '@tabler/icons-vue'
import type { StatusUpdate } from './ChatMessage.vue'

const { t } = useI18n()

const props = defineProps<{
  statusUpdates: StatusUpdate[]
  isComplete: boolean
}>()

const isExpanded = ref(false)

const showStatus = computed(() => {
  return props.statusUpdates.length > 0
})

const currentStatusText = computed(() => {
  if (!props.statusUpdates?.length) return ''
  return formatStatusAction(props.statusUpdates[props.statusUpdates.length - 1])
})

const thoughtTimeInSeconds = computed(() => {
  if (props.statusUpdates.length === 0) return 0
  const firstUpdate = props.statusUpdates[0]
  const lastUpdate = props.statusUpdates[props.statusUpdates.length - 1]
  if (!firstUpdate.timestamp || !lastUpdate.timestamp) return 0
  const diffMs = lastUpdate.timestamp.getTime() - firstUpdate.timestamp.getTime()
  return Math.round(diffMs / 1000)
})

const toggleExpanded = () => {
  isExpanded.value = !isExpanded.value
}

const formatStatusAction = (status: StatusUpdate): string => {
  switch (status.action) {
    case 'statusProcessing':
      return t('statusProcessing')
    case 'preModelHook':
      return t('statusPreModel')
    case 'planning':
      return t('planning', { tool: status.toolName })
    case 'executingTool':
      return t('statusExecutingTool', { tool: status.toolName }) 
      + (status.step ? " - " + t(status.step) : '') 
      + (status.args? t('withParams', { params: status.args })  : '')
    case 'executedTool':
      return t('statusExecutedTool', { tool: status.toolName })
    case 'toolError':
      return t('toolError', { tool: status.toolName})
    default:
      return status.action
  }
}

watch(() => props.isComplete, (newIsComplete) => {
  if (newIsComplete) {
    isExpanded.value = false
  }
})
</script>

<template>
  <div v-if="showStatus" class="status-container mb-2">
    <div class="border border-auxiliar-gray rounded-lg overflow-hidden">
      <button @click="toggleExpanded" class="w-full flex items-center justify-between px-3 py-2 bg-pale hover:bg-auxiliar-gray transition-colors":class="{ 'bg-transparent': !isComplete }">
        <div v-if="!isComplete" class="flex items-center gap-2">
          <div class="w-3 h-3 border-2 border-auxiliar-gray border-t-transparent rounded-full animate-spin"></div>
          <span class="text-sm text-light-gray">{{ currentStatusText }}</span>
        </div>
        <div v-else class="flex items-center gap-2">
          <img src="@/assets/images/status-icon.svg" alt="status"/>
          <span class="text-sm font-medium text-light-gray">
            {{ thoughtTimeInSeconds > 0 ? t('endMessage', { time: thoughtTimeInSeconds }) : t('thoughtProcessMessage') }}
          </span>
        </div>
        <IconChevronDown :class="['w-4 h-4 transition-transform', { 'rotate-180': isExpanded }]" />
      </button>
      <div v-if="isExpanded" class="border-t border-auxiliar-gray">
        <div class="p-3 space-y-2 overflow-y-auto" :class="{ 'max-h-60': isComplete }">
          <div v-for="(status, index) in statusUpdates" :key="index" class="flex items-start gap-2 text-sm">
            <div class="flex-1">
              <div class="font-medium text-lighter-gray">{{ index + 1 }}. {{ formatStatusAction(status) }}</div>
              <div v-if="status.description && status.description.trim() !== ''"
                class="pl-4 font-medium text-lighter-gray">
                <span>{{ t('description') }}: </span> <span class="italic">{{ status.description }}</span>
              </div>
              <div v-if="status.result && (typeof status.result === 'string' ? status.result.trim() !== '' : false)" class="pl-4 font-medium text-lighter-gray">
                {{ t('result') }} {{ status.result }}
              </div>
              <div v-if="status.result && Array.isArray(status.result) && status.result.length > 0"
                class="pl-4 font-medium text-lighter-gray">
                <div v-for="doc in status.result" class="flex items-start gap-2 text-sm">
                  <div class="font-medium text-lighter-gray">- {{ doc }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<i18n lang="json">
{
  "en": {
    "statusProcessing": "Processing",
    "statusPreModel": "Thinking",
    "planning": "Planning to run tools",
    "statusExecutingTool": "Executing {tool}",
    "statusExecutedTool": "Tool {tool} execution finished",
    "documentsRetrieved": "{count} chunks retrieved",
    "toolError": "Error in tool {tool}",
    "endMessage": "Thought for {time} seconds",
    "result": "Result:",
    "results": "Results {count}:",
    "description": "Description",
    "retrieving": "Retrieving chunks",
    "retrieved": "Chunks retrieved",
    "analyzing": "Analyzing chunks",
    "analyzed": "Chunks analyzed",
    "groundingResponse": "Validating response",
    "groundedResponse": "Response validated",
    "withParams": " with params {params}",
    "thoughtProcessMessage": "Thought process"
  },
  "es": {
    "statusProcessing": "Procesando",
    "statusPreModel": "Pensando",
    "planning": "Planificando ejecutar herramientas",
    "statusExecutingTool": "Ejecutando {tool}",
    "statusExecutedTool": "Ejecución de herramienta {tool} finalizada",
    "documentsRetrieved": "{count} secciones recuperados",
    "toolError": "Error en la herramienta {tool}",
    "endMessage": "Pensó durante {time} segundos",
    "result": "Resultado:",
    "results": "Resultados {count}:",
    "retrieving": "Recuperando secciones",
    "retrieved": "Secciones recuperadas",    
    "analyzing": "Analizando secciones",
    "analyzed": "Secciones analizadas",
    "groundingResponse": "Validando respuesta",
    "groundedResponse": "Respuesta validada",
    "description": "Descripción",
    "withParams": " con los siguientes parametros {params}",
    "thoughtProcessMessage": "Proceso de pensamiento"
  }
}
</i18n>
