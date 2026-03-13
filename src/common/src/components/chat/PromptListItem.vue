<script lang="ts" setup>
import { ref } from "vue";
import { useI18n } from "vue-i18n";
import type { Menu } from "primevue";
import type { MenuItem } from "primevue/menuitem";
import {
  IconWorldUpload,
  IconLock,
  IconEdit,
  IconTrash,
  IconPlayerPlay,
  IconDots,
} from "@tabler/icons-vue";
import { AnimationEffect } from "../../utils/animations";
import { AgentPrompt } from "../../utils/domain";

const { t } = useI18n();

const props = defineProps<{
  prompt: AgentPrompt;
  selected: boolean;
  readonly?: boolean;
}>();
const emit = defineEmits<{
  (e: "select", prompt: AgentPrompt): void;
  (e: "delete", id: number): void;
  (e: "edit", prompt: AgentPrompt): void;
}>();

const showPromptConfirmation = ref<boolean>(false);
const menuItems = ref<MenuItem[]>([
  {
    label: t("editPrompt"),
    tablerIcon: IconEdit,
    command: () => {
      emit("edit", props.prompt);
    },
  },
  {
    label: t("deletePrompt"),
    tablerIcon: IconTrash,
    command: () => {
      showPromptConfirmation.value = true;
    },
  },
]);
const menu = ref<InstanceType<typeof Menu>>();

const deletePrompt = () => {
  showPromptConfirmation.value = false;
  emit("delete", props.prompt.id!);
};

function handlePromptClick(e: MouseEvent) {
  e.preventDefault();
  emit("select", props.prompt);
}
</script>
<template>
  <ListItem
    v-if="!showPromptConfirmation"
    class="group p-3 py-0 mb-1"
    :class="selected ? 'bg-surface-muted' : ''"
    @click="handlePromptClick($event)"
  >
    <template #start>
      <IconWorldUpload v-if="prompt.shared" class="w-5 h-5 flex-shrink-0"/>
      <IconLock v-else class="w-5 h-5 flex-shrink-0"/>
    </template>
    <span>{{ prompt.name }}</span>
    <template #end>
      <div v-if="prompt.starter" class="flex items-center gap-1">
        <IconPlayerPlay class="w-4 h-4 text-content-muted" />
        <span class="text-sm text-content-muted">{{ t("starterText") }}</span>
      </div>
      <div v-if="prompt.canEdit && !prompt.starter && !readonly"
        class="opacity-0 group-hover:opacity-100 transition-opacity"
        @click.stop="menu?.toggle($event)">
        <IconDots />
      </div>
      <Menu v-if="prompt.canEdit && !prompt.starter && !readonly"
        ref="menu"
        :model="menuItems"
        :popup="true">
        <template #item="{ item }">
          <MenuItemTemplate :item="item" />
        </template>
      </Menu>
    </template>
  </ListItem>
  <Animate v-else :effect="AnimationEffect.QUICK_SLIDE_DOWN">
    <ItemConfirmation
      class="shadow-none !m-0 !rounded-lg"
      :tooltip="t('deletePromptConfirmation')"
      @confirm="deletePrompt"
      @cancel="() => (showPromptConfirmation = false)"/>
  </Animate>
</template>

<i18n lang="json">
{
  "en": {
    "editPrompt": "Edit prompt",
    "deletePrompt": "Delete prompt",
    "starterText": "Starter",
    "deletePromptConfirmation": "Delete prompt?"
  },
  "es": {
    "editPrompt": "Editar prompt",
    "deletePrompt": "Borrar prompt",
    "starterText": "Iniciador",
    "deletePromptConfirmation": "Borrar prompt?"
  }
}
</i18n>
