<script lang="ts" setup>
import { useDebounce } from '@/composables/useDebounce';
import { ApiService, type Agent, type Thread } from '@/services/api';
import { onMounted, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n'

const props = defineProps<{
    agent: Agent,
    currentChat: Thread,
}>()
const emit = defineEmits<{
    (e: "close"): void
    (e: "selectChat", chat: Thread): void
}>()

const { t } = useI18n();
const api = new ApiService();
const chats = ref<Thread[]>([])
const searchVal = ref<string>("");
const isLoading = ref<boolean>(true);
const isSearching = ref<boolean>(false);

onMounted(async () => {
    debouncedSearch()
})

const debouncedSearch = useDebounce(async () => {
    chats.value = await api.findChatsByText(searchVal.value.trim(), 10, true, props.agent.id)
    isSearching.value = false;
    isLoading.value = false;
});

watch(() => searchVal.value, () => {
    isSearching.value = true;
    debouncedSearch();
});

const handleChatClick = (chat: Thread) => {
    emit("selectChat", chat)
}
</script>

<template>
    <FlexCard class="pb-4 !w-[500px] !h-auto z-10 max-h-[380px]" v-click-outside="()=>emit('close')"
        header-height="auto">
        <template #header>
            <div class="flex items-center gap-2">
                <div class="flex-grow relative">
                    <IconLoader v-if="isSearching"
                        class="absolute left-3 top-1/2 -translate-y-1/2 text-content-muted animate-spin" />
                    <IconSearch v-else class="absolute top-1/2 -translate-y-1/2 left-3 text-content-muted" />
                    <input v-model="searchVal" class="pl-11 w-full border-1 rounded-lg px-3 py-3"
                        :placeholder="t('searchChatPlaceholder', { agentName: props.agent.name || '' })" />
                </div>
                <SimpleButton @click="emit('close')">
                    <IconX />
                </SimpleButton>
            </div>
        </template>
        <div v-if="isLoading" class="flex justify-center">
            <IconLoader class="text-content-muted animate-spin" />
        </div>
        <div v-else>
            <div v-if="chats.length > 0" class="flex flex-col max-h-[250px] overflow-y-auto">
                <div v-for="chat in chats">
                    <ListItem class="mb-1" :class="currentChat.id == chat.id ? 'bg-surface-muted' : ''"
                        @click="handleChatClick(chat)">
                        {{ chat.name }}
                    </ListItem>
                </div>
            </div>
            <div class="p-3 text-content-muted" v-else>
                {{ t('noChats') }}
            </div>
        </div>
    </FlexCard>
</template>

<i18n>
    {
        "en":{
            "searchChatPlaceholder": "Search chats from agent {agentName}",
            "noChats": "No chats found"
        },
        "es":{
            "searchChatPlaceholder": "Buscar chats del agente {agentName}",
            "noChats": "No se encontraron chats"
        }
    }
</i18n>

<style lang="scss">
.input-icon {}
</style>
