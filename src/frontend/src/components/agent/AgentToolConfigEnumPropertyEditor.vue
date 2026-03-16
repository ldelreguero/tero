<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import type { MenuItem } from 'primevue/menuitem';
import { IconX } from '@tabler/icons-vue';

const props = defineProps<{
  id: string;
  modelValue: string[] | undefined;
  label: string;
  optionValues: string[];
  optionLabels: (propName: string, value: string) => string;
  viewMode?: boolean;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: string[]): void
}>();

const { t } = useI18n()
const menu = ref()
const menuItems = ref<MenuItem[]>([])
const safeModelValue = computed(() => props.modelValue || [])

onMounted(async () => {
  updateMenuItems()
})

const updateMenuItems = () => {
  menuItems.value = props.optionValues.filter(val => !safeModelValue.value.includes(val)).map( (val : string) => ({
      label: props.optionLabels(props.id, val),
      command: () => onAddOption(val)
  }))
}

const onAddOption = (val: string) => {
  emit('update:modelValue', [...safeModelValue.value, val])
}

watch(() => props.modelValue, () => {
  updateMenuItems()
})

const onClickAddOption = () => {
  menu.value?.toggle(event)
}

const onRemoveOption = (val: string) => {
  emit('update:modelValue', safeModelValue.value.filter(option => option !== val))
}
</script>

<template>
  <div class="flex items-center justify-between w-full mb-2">
    <label > {{ label }} </label>
    <SimpleButton
      v-if="!viewMode"
      size="small"
      shape="square"
      class="px-3"
      :disabled="safeModelValue.length === props.optionValues.length"
      @click="onClickAddOption">
        <IconPlus/> {{ t('addOption') }}
    </SimpleButton>
  </div>
  <div class="flex flex-col gap-2">
    <div v-if="safeModelValue.length === 0" class="text-sm text-content-muted">
      <div>{{ t('noOptions') }}</div>
    </div>
    <div v-else class="flex flex-row flex-wrap gap-2 w-0 min-w-full">
      <div v-for="option in safeModelValue" :key="option" class="relative rounded-xl border-1">
        <div class="flex justify-between items-center p-2 gap-2">
          <div class="flex flex-row items-center gap-2">
            <span>{{ optionLabels(id, option) }}</span>
          </div>
          <div v-if="!viewMode" class="flex flex-row justify-center items-center border-l pl-2 gap-2">
            <SimpleIcon interactive @click="onRemoveOption(option)" :icon="IconX" class="hover:text-error-alt"/>
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
</template>


<i18n lang="json">
  {
    "en": {
      "addOption": "Add",
      "noOptions": "No values have been selected"
    },
    "es": {
      "addOption": "Agregar",
      "noOptions": "No se han seleccionado valores"
    }
  }
</i18n>
