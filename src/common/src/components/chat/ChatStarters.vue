<script setup lang="ts">
import { AgentPrompt } from '../../utils/domain';
import { useI18n } from 'vue-i18n';
import ChatInput from './ChatInput.vue';

const { t } = useI18n();

const props = defineProps<{
  promptsStarters: AgentPrompt[],
  chatInputRef: InstanceType<typeof ChatInput>
}>()

</script>
<template>
  <div  class="flex flex-col gap-4 md:gap-8 items-start max-w-[837px] md:mx-auto p-2 md:p-0">
      <p class="text-left whitespace-pre-line text-base md:text-lg">
        {{ t('starterText') }}
      </p>
      <div class="w-full flex flex-col md:flex-wrap md:flex-row gap-4 text-content-muted">
        <div v-for="prompt in promptsStarters" :key="prompt.id">
          <button
            @click="chatInputRef?.selectPrompt(prompt)"
            class="w-full md:w-[185px] h-[74px] md:h-[94px] rounded-lg border p-3 text-left hover:border-abstracta shadow flex items-start">
              <span class="line-clamp-2 md:line-clamp-3 text-sm md:text-base">
                {{ prompt.name }}
              </span>
          </button>
        </div>
      </div>
  </div>
</template>

<i18n lang="json">
  {
    "en": {
      "starterText": "Hi! 👋 \n How can I help you?"
    },
    "es": {
      "starterText": "Hola! 👋 \n ¿Cómo puedo ayudarte?"
    }
  }
</i18n>

