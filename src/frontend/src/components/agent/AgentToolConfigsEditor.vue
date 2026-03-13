<script setup lang="ts">
import { onMounted, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import type { MenuItem } from 'primevue/menuitem';
import { ApiService } from '@/services/api';
import { AgentToolConfig, type AgentTool } from '@/services/api';
import { useErrorHandler } from '@/composables/useErrorHandler';
import { type Icon } from '@tabler/icons-vue';
import { EditingToolConfig } from './AgentToolConfigEditor.vue';
import { IconEditCircle, IconEye, IconX } from '@tabler/icons-vue';
import { useToolConfig } from '@/composables/useToolConfig';

const { t } = useI18n()
const api = new ApiService()
const { handleError } = useErrorHandler()
const { findToolIcon, buildToolConfigName } = useToolConfig();

const props = defineProps<{
  agentId: number;
  toolConfigs: AgentToolConfig[];
  viewMode?: boolean;
}>();

const emit = defineEmits<{
  (e: 'update'): void
}>()

const menu = ref()
const availableTools = ref<AgentTool[]>([])
const menuItems = ref<MenuItem[]>([])
const editingToolConfig = ref<EditingToolConfig | null>(null)
const deletingToolConfig = ref<string | null>(null)

onMounted(async () => {
  try {
    availableTools.value = await api.findAgentTools()
    updateMenuItems()
  } catch (error) {
    handleError(error)
  }
})

const updateMenuItems = () => {
  menuItems.value = availableTools.value.filter(tool => !props.toolConfigs.some(config => config.toolId === tool.id)).map( (tool: AgentTool) => {
    const toolName = buildToolConfigName(tool.id)
    const toolIcon = findToolIcon(tool.id)
    return {
      label: toolName,
      tablerIcon: toolIcon,
      command: () => onConfigureNewTool(tool, toolName, toolIcon)
    }
  }).sort((a, b) => a.label.localeCompare(b.label))
}

watch(() => props.toolConfigs, () => {
  updateMenuItems()
})

const onConfigureNewTool = (tool: AgentTool, toolName: string, toolIcon: Icon) => {
  editingToolConfig.value = new EditingToolConfig(props.agentId, tool, toolName, toolIcon)
}

const onAddTool = (event: Event) => {
  menu.value?.toggle(event)
}

const onSaveToolConfig = async() => {
  onCloseToolConfig()
  emit('update')
}

const onCloseToolConfig = () => {
  editingToolConfig.value = null
}

const onEditToolConfig = (toolConfig: AgentToolConfig) => {
  const tool = getToolById(toolConfig.toolId)
  editingToolConfig.value = new EditingToolConfig(props.agentId, tool!, buildToolConfigName(tool.id), findToolIcon(tool.id), toolConfig)
}

const hasConfigurableProperties = (toolId: string) : boolean=> {
  const tool = getToolById(toolId)
  return !!(tool?.configSchema?.properties && Object.keys(tool.configSchema.properties).length > 0)
}

const getToolById = (toolId: string) : AgentTool => {
  return availableTools.value.find(tool => (tool.id.endsWith("-*") && toolId.startsWith(tool.id.split("-", 1)[0])) || tool.id === toolId)!
}

const onDeleteToolConfig = (toolConfig: AgentToolConfig) => {
  deletingToolConfig.value = toolConfig.toolId
}

const onConfirmDelete = async (toolId: string) => {
  deletingToolConfig.value = null
  try {
    await api.removeAgentToolConfig(props.agentId, toolId)
    emit('update')
  } catch (error) {
    handleError(error)
  }
}

const onCancelDelete = () => {
  deletingToolConfig.value = null
}
</script>

<template>
  <div class="flex items-center justify-between w-full mb-2" v-if="!viewMode">
    <label > {{ t('toolsLabel') }} </label>
    <SimpleButton
      size="small"
      shape="square"
      class="px-3"
      @click="onAddTool">
        <IconPlus/> {{ t('addTool') }}
    </SimpleButton>
  </div>
  <div class="flex flex-col gap-2">
    <div v-if="toolConfigs.length === 0" class="text-sm text-content-muted">
      <div>{{ t('noTools') }}</div>
    </div>
    <div v-else class="flex flex-row flex-wrap gap-2 w-0 min-w-full">
      <div v-for="tool in toolConfigs" :key="tool.toolId" class="relative rounded-xl border-1">
        <!-- using absolute position flex and inset in confirmation and invisible in item with py to keep item confirmation the same size as element -->
        <ItemConfirmation
              v-if="deletingToolConfig === tool.toolId"
              class="shadow-none !m-0 border-none flex-1 absolute inset-0"
              :tooltip="t('deleteToolConfigConfirmation')"
              @confirm="() => onConfirmDelete(tool.toolId)"
              @cancel="onCancelDelete"
            />
        <div class="flex justify-between items-center py-3 px-2 min-w-45" :class="{'invisible': deletingToolConfig === tool.toolId}">
          <div class="flex flex-row items-center gap-2 pr-2">
            <div>
              <component :is="findToolIcon(tool.toolId)"/>
            </div>
            <span>{{ buildToolConfigName(tool.toolId) }}</span>
          </div>
          <div class="flex flex-row justify-center items-center border-l pl-2 gap-2">
            <SimpleIcon interactive v-if="hasConfigurableProperties(tool.toolId)" @click="onEditToolConfig(tool)" v-tooltip.bottom="viewMode ? t('viewToolConfig') : t('editToolConfig')" :icon="viewMode ? IconEye : IconEditCircle" />
            <SimpleIcon interactive @click="onDeleteToolConfig(tool)" v-tooltip.bottom="t('deleteToolConfig')" :icon="IconX" class="hover:text-error-alt" v-if="!viewMode"/>
          </div>
        </div>
      </div>
    </div>
  </div>

  <Menu ref="menu" :model="menuItems" :popup="true" class="!min-w-10">
    <template #item="{ item }">
      <MenuItemTemplate :item="item"/>
    </template>
  </Menu>

  <Dialog :visible="editingToolConfig !== null" @update:visible="onCloseToolConfig" :modal="true" :draggable="false" :resizable="false" :closable="false" class="basic-dialog" maximizable :style="{ width: '40rem' }" :dismissableMask="true">
    <AgentToolConfigEditor v-if="editingToolConfig"
      :toolConfig="editingToolConfig"
      @update="onSaveToolConfig"
      @close="onCloseToolConfig"
      :viewMode="viewMode"
    />
  </Dialog>
</template>

<i18n lang="json">
  {
    "en": {
      "toolsLabel": "Tools",
      "addTool": "Add",
      "noTools": "No configured tools",
      "editToolConfig": "Edit",
      "viewToolConfig": "View",
      "deleteToolConfig": "Remove",
      "deleteToolConfigConfirmation": "Remove?"
    },
    "es": {
      "toolsLabel": "Herramientas",
      "addTool": "Agregar",
      "noTools": "No hay herramientas configuradas",
      "editToolConfig": "Editar",
      "viewToolConfig": "Ver",
      "deleteToolConfig": "Quitar",
      "deleteToolConfigConfirmation": "¿Quitar?"
    }
  }
</i18n>
