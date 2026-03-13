<script lang="ts" setup>
import { ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { IconBook2, IconPlus } from '@tabler/icons-vue';
import { AgentPrompt } from '../../utils/domain';

const props = defineProps<{
  prompts: AgentPrompt[]
  selectedPromptIndex: number
  readonly?: boolean
}>()
const emit =defineEmits<{
  (e: 'promptCreate'): void
  (e: 'promptSelect', prompt: AgentPrompt): void
  (e: 'promptDelete', id: number): void
  (e: 'promptEdit', prompt: AgentPrompt): void
}>()

const { t } = useI18n();
const itemRefs = ref<HTMLElement[]>([]);

const scrollSelectedIntoView = () => {
  const selectedElement = itemRefs.value[props.selectedPromptIndex];
  if (selectedElement) {
    selectedElement.scrollIntoView({
      behavior: 'smooth',
      block: 'nearest'
    });
  }
};

watch(()=>props.selectedPromptIndex, scrollSelectedIntoView)

</script>

<template>
    <FlexCard>
        <template #header>
            <div class="flex w-full items-center justify-between">
                <div class="flex gap-2 items-center">
                    <IconBook2 />
                    <span class="text-lg">Prompts</span>
                </div>
                <div v-if="!readonly">
                    <SimpleButton @click="emit('promptCreate')" variant="primary" shape="rounded">
                        <IconPlus />
                        <span class="mx-1">
                            {{ t('createPromptButton') }}
                        </span>
                    </SimpleButton>
                </div>
            </div>
        </template>
        <div class="flex flex-col h-full max-h-[300px] pb-4">
            <div v-if="props.prompts.length > 0" class="overflow-y-auto">
                <div v-for="(prompt, index) in prompts" ref="itemRefs">
                    <PromptListItem :prompt="prompt" :selected="index === selectedPromptIndex"
                        :readonly="readonly"
                        @delete="emit('promptDelete', $event)"
                        @select="emit('promptSelect', $event)"
                        @edit="emit('promptEdit', $event)"></PromptListItem>
                </div>
            </div>
            <div v-else class="flex justify-center items-center">
                <span>{{ t('noPrompts') }}</span>
            </div>
        </div>
    </FlexCard>
</template>

<i18n lang="json">
    {
        "en":{
            "createPromptButton": "Create prompt",
            "noPrompts": "No prompts"
        },
        "es":{
            "createPromptButton": "Crear prompt",
            "noPrompts": "No hay prompts"
        }
    }
</i18n>
