<script lang="ts" setup>
import { computed, ref, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { LlmModel, LlmModelVendor, LlmTemperature, ReasoningEffort } from '@/services/api'
import openAiIcon from '@/assets/images/open-ai.svg?raw'
import googleIcon from '@/assets/images/gemini.svg?raw'
import anthropicIcon from '@/assets/images/anthropic.svg?raw'
import qwenIcon from '@/assets/images/qwen.svg?raw'
import openAiIsotipo from '@/assets/images/openai-iso.svg?raw'
import googleIsotipo from '@/assets/images/gemini-iso.svg?raw'
import anthropicIsotipo from '@/assets/images/anthropic-iso.svg?raw'
import qwenIsotipo from '@/assets/images/qwen-iso.svg?raw'
import LlmModelSettings from './LlmModelSettings.vue'
import GroupedSelectPanel, { type GroupedSelectPanelOptionGroup } from '@/components/common/GroupedSelectPanel.vue'

const props = defineProps<{
  modelId?: string
  models: LlmModel[]
  temperature?: LlmTemperature
  reasoningEffort?: ReasoningEffort
}>()

const emit = defineEmits<{
  (e: 'update:modelId', value: string): void
  (e: 'update:temperature', value: LlmTemperature): void
  (e: 'update:reasoningEffort', value: ReasoningEffort): void
  (e: 'change'): void
}>()

const { t } = useI18n()

const showAllModels = ref(false)
const searchQuery = ref('')

const selectedModel = computed(() => props.models.find((m) => m.id === props.modelId))

const updateShowAllModels = () => {
  if (selectedModel.value && !selectedModel.value.isBasic) {
    showAllModels.value = true
  } else if (!selectedModel.value) {
    showAllModels.value = false
  }
}

watch(() => props.modelId, () => {
  updateShowAllModels()
})

onMounted(() => {
  updateShowAllModels()
})

const modelType = computed(() => selectedModel.value?.modelType)

const vendorLogos: Record<LlmModelVendor, { logo: string; isotipo: string }> = {
  [LlmModelVendor.OPENAI]: { logo: openAiIcon, isotipo: openAiIsotipo },
  [LlmModelVendor.GOOGLE]: { logo: googleIcon, isotipo: googleIsotipo },
  [LlmModelVendor.ANTHROPIC]: { logo: anthropicIcon, isotipo: anthropicIsotipo },
  [LlmModelVendor.QWEN]: { logo: qwenIcon, isotipo: qwenIsotipo }
}

const groupByVendor = (models: LlmModel[]): Map<LlmModelVendor, LlmModel[]> => {
  const map = new Map<LlmModelVendor, LlmModel[]>()
  for (const model of models) {
    const list = map.get(model.modelVendor)
    if (list) list.push(model)
    else map.set(model.modelVendor, [model])
  }
  return map
}

const groupedModelOptions = computed<GroupedSelectPanelOptionGroup[]>(() => {
  let list: LlmModel[]
  if (showAllModels.value) {
    list = props.models
  } else {
    const basic = props.models.filter((m) => m.isBasic)
    const selected = selectedModel.value
    list = selected && !selected.isBasic && !basic.some((m) => m.id === selected.id) ? [...basic, selected] : basic
  }

  const q = searchQuery.value.trim().toLowerCase()
  if (q) {
    list = list.filter(({ modelVendor, name }) => [modelVendor?.toString(), name].some((v) => v?.toLowerCase().includes(q)))
  }
  return [...groupByVendor(list).entries()].map(([vendor, models]) => ({
    id: vendor,
    icon: vendorLogos[vendor]!.logo,
    name: vendor,
    children: models.map((model) => ({
      id: model.id,
      name: model.name,
      description: model.description
    }))
  }))
})

const groupedSelectPanelRef = ref<InstanceType<typeof GroupedSelectPanel>>()

const onShowAllModels = () => {
  groupedSelectPanelRef.value?.onShowDropdown()
}

const onModelChange = (value: string) => {
  emit('update:modelId', value)
  emit('change')
  groupedSelectPanelRef.value?.onShowDropdown()
}

const onSearch = (value: string) => {
  searchQuery.value = value
  if (value?.trim()) {
    showAllModels.value = true
  }
}

const containerRef = ref<HTMLDivElement>()
const selectedOptionId = computed(() => selectedModel.value?.id ?? null)
const visibleOptions = computed(() => groupedModelOptions.value.filter((option) => option.children!.length > 0))
</script>

<template>
  <div class="flex flex-row gap-3 relative" ref="containerRef">
    <div class="form-field flex-1">
      <label for="model">{{ t('modelLabel') }}</label>
      <button class="flex items-center w-full border rounded-xl p-2 justify-between focus:border-abstracta" type="button" @click="onShowAllModels">
        <span class="flex flex-row items-center gap-2">
          <span v-html="vendorLogos[selectedModel?.modelVendor as LlmModelVendor]!.isotipo" class="flex items-center" />
          {{ selectedModel?.name }}
        </span>
        <IconCaretDown class="fill-abstracta border-none" />
      </button>
      <GroupedSelectPanel ref="groupedSelectPanelRef" :search-placeholder="t('searchPlaceholder')" :container="containerRef" :show-load-more="!showAllModels && models.some((m) => !m.isBasic)" @search="onSearch" @load-more="showAllModels = true">
        <template #content>
          <div v-if="visibleOptions.length > 0" class="flex flex-row items-center gap-2">
            <div class="flex flex-col items-stretch w-full">
              <div v-for="(option, index) in visibleOptions" :key="option.id" class="py-3" :class="[index < visibleOptions.length - 1 && 'border-b-2 border-dotted']">
                <div class="flex flex-row items-start gap-3 w-full">
                  <div class="w-36 shrink-0 pt-2 flex items-center gap-2">
                    <span v-if="typeof option.icon === 'string'" v-html="option.icon" class="flex items-center" />
                    <component v-else :is="option.icon" class="flex items-center" />
                  </div>
                  <div class="flex-1 min-w-0 flex flex-col gap-2">
                    <div
                      v-for="optionItem in option.children"
                      :key="optionItem.id"
                      class="flex flex-col gap-2 hover:bg-surface-muted rounded-2xl p-2 px-4 cursor-pointer"
                      :class="{ 'bg-surface-muted': selectedOptionId === optionItem.id }"
                      @click="onModelChange(optionItem.id)"
                    >
                      <span v-if="optionItem.name" class="font-semibold">{{ optionItem.name }}</span>
                      <span>{{ optionItem.description }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="text-sm text-content-muted text-center py-2 min-h-[30vh] flex items-center justify-center">
            {{ t('noOptionsPlaceholder') }}
          </div>
        </template>
      </GroupedSelectPanel>
    </div>
    <div class="form-field w-1/2">
      <LlmModelSettings
        :model-type="modelType"
        :temperature="temperature"
        :reasoning-effort="reasoningEffort"
        @update:temperature="(value) => emit('update:temperature', value)"
        @update:reasoning-effort="(value) => emit('update:reasoningEffort', value)"
        @change="emit('change')"
      />
    </div>
  </div>
</template>

<i18n lang="json">
{
  "en": {
    "modelLabel": "Model",
    "searchPlaceholder": "Search model...",
    "noOptionsPlaceholder": "No models found"
  },
  "es": {
    "modelLabel": "Modelo",
    "searchPlaceholder": "Buscar modelo...",
    "noOptionsPlaceholder": "No se han encontrado modelos"
  }
}
</i18n>
