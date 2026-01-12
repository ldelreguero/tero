<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { IconX } from '@tabler/icons-vue';

const { t } = useI18n();


const props = defineProps<{
  title: string;
  showModal: boolean;
  isLoading: boolean;
  hasMoreData?: boolean;
  loadingMoreData?: boolean;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'loadMoreData'): void;
}>();
</script>

<template>
  <Dialog :visible="props.showModal" @update:visible="emit('close')" :modal="true" :draggable="false" :resizable="false" :closable="false" :close-on-escape="true" class="w-150 basic-dialog" :show-header="false" :dismissable-mask="true">
      <div class="flex flex-col bg-surface rounded-xl">
        <div class="flex items-center gap-2 justify-between w-full p-5">
          <div class="flex flex-row gap-2 items-start flex-1 min-w-0">
            <slot name="avatar" />
            <div class="flex flex-col min-w-0 gap-1">
              <span class="font-semibold text-2xl truncate min-w-0 max-w-full block">{{ props.title }}</span>
              <div class="flex gap-1 text-light-gray text-xs w-fit">
                <slot name="subtitle" />
              </div>
            </div>
          </div>
          <div class="flex flex-row gap-4 justify-start h-full self-start flex-shrink-0">
            <SimpleButton size="small" shape="rounded" @click="emit('close')" >
              <IconX class="w-6 h-6" />
            </SimpleButton>
          </div>
        </div>
        <div class="flex gap-4 px-5 py-4 border-b border-t border-auxiliar-gray">
          <slot name="summary" />
        </div>
        <div class="flex flex-col gap-2 px-5 py-4 min-h-[256px]">
          <div class="animate-pulse space-y-6 flex flex-col gap-2" v-if="props.isLoading">
            <div v-for="n in 5" :key="n" class="flex flex-col bg-auxiliar-gray rounded animate-pulse w-full h-8">
            </div>
          </div>
          <slot name="details" v-else />
        </div>
        <div class="flex flex-row gap-2 items-center justify-between p-5" :class="{ 'justify-end': !props.hasMoreData }">
          <SimpleButton v-if="props.hasMoreData && !props.isLoading" :disabled="props.loadingMoreData" size="small" shape="square" class="px-3" @click=" emit('loadMoreData')">
            <span v-if="props.loadingMoreData">{{ t('loadingMore') }}</span>
            <span v-else>{{ t('loadMore') }}</span>
          </SimpleButton>
          <slot name="footerAction" />
        </div>
      </div>
  </Dialog>
</template>

<i18n lang="json">
  {
    "en": {
      "loadMore": "Load more",
      "loadingMore": "Loading more..."
    },
    "es": {
      "loadMore": "Cargar más",
      "loadingMore": "Cargando más..."
    }
  }
</i18n>
