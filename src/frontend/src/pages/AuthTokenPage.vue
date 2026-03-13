<script setup lang="ts">
import { ref, onBeforeMount } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Dialog } from 'primevue'
import SimpleButton from '../../../common/src/components/common/SimpleButton.vue'
import InteractiveInput from '../../../common/src/components/common/InteractiveInput.vue'
import { ApiService } from '@/services/api'
import { useToolConfig } from '@/composables/useToolConfig'

const route = useRoute()
const { t } = useI18n()
const authToken = ref('')
const isVisible = ref(true)
const isSubmitting = ref(false)

const toolId = route.params.toolId as string
const agentId = parseInt(route.params.agentId as string)
const api = new ApiService()
const { buildToolConfigName } = useToolConfig()

let channel: BroadcastChannel | null = null

const handleSubmit = async () => {
  if (!authToken.value.trim() || isSubmitting.value) {
    return
  }

  isSubmitting.value = true
  try {
    await api.completeToolAuthTokenAuth(toolId, agentId, authToken.value)
    sendMessage(true)
  } catch (error) {
    console.error(error)
    isSubmitting.value = false
    sendMessage(false, false)
  }
}

const handleCancel = () => {
  sendMessage(false, true)
}

onBeforeMount(() => {
  channel = new BroadcastChannel('auth_token_channel')

  window.addEventListener('beforeunload', () => {
    // This is to handle the case where the user closes the window without submitting the token
    sendMessage(false, true)
  })
})

const sendMessage = (success: boolean, cancelled = false) => {
  if (!channel) return
  try {
    channel.postMessage({
      type: 'auth_token_result',
      toolId,
      agentId,
      success,
      cancelled
    })
  } finally {
    cleanup()
    window.close()
  }
}

const cleanup = () => {
  if (channel) {
    channel.close()
    channel = null
  }
}

</script>

<template>
  <div class="flex items-center justify-center h-screen">
    <Dialog
      v-model:visible="isVisible"
      :modal="true"
      :draggable="false"
      :resizable="false"
      :closable="false"
      class="basic-dialog"
      :showHeader="false"
      :dismissableMask="true"
      @update:visible="handleCancel"
    >
      <div class="flex flex-col gap-4 bg-surface rounded-xl p-4 pt-6">
        <h2 class="text-xl font-semibold m-0">{{ t('toolAuthentication') }}</h2>
        <p class="text-content-muted m-0">{{ t('enterToken', { serverName: buildToolConfigName(toolId) }) }}</p>
        <form @submit.prevent="handleSubmit" class="flex flex-col gap-4">
          <div class="flex flex-col gap-1">
            <label for="authToken">Token</label>
            <InteractiveInput
              id="authToken"
              v-model="authToken"
              type="password"
              required
              autofocus
            />
          </div>
          <div class="flex flex-row gap-2 items-center justify-end">
            <SimpleButton @click="handleCancel" shape="square" :disabled="isSubmitting">{{ t('cancel') }}</SimpleButton>
            <SimpleButton @click="handleSubmit" variant="primary" shape="square" type="submit" :disabled="isSubmitting">{{ t('submit') }}</SimpleButton>
          </div>
        </form>
      </div>
    </Dialog>
  </div>
</template>

<i18n lang="json">
  {
    "en": {
      "toolAuthentication": "Tool Authentication",
      "enterToken": "Please enter the token required to use {serverName}",
      "cancel": "Cancel",
      "submit": "Submit"
    },
    "es": {
      "toolAuthentication": "Autenticación de Herramienta",
      "enterToken": "Por favor ingrese el token requerido para usar {serverName}",
      "cancel": "Cancelar",
      "submit": "Enviar"
    }
  }
</i18n>
