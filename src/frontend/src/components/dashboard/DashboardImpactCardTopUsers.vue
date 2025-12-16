<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { ref, onMounted, watch } from 'vue';
import { UserImpactItem, AgentImpactItem } from '@/services/api';
import { ApiService } from '@/services/api';
import { useErrorHandler } from '@/composables/useErrorHandler';
import { useDebounce } from '@/composables/useDebounce';
import { IconInfoCircle } from '@tabler/icons-vue';

const { t } = useI18n();
const { handleError } = useErrorHandler();
const api = new ApiService();

const props = defineProps<{ 
    fromDate: Date;
    toDate: Date;
    teamId: number;
}>();

const loading = ref<boolean>(false);
const topUsers = ref<UserImpactItem[]>([]);
const userPage = ref<number>(1);
const pageSize = 20;
const loadingMoreUsers = ref<boolean>(false);
const hasMoreUsers = ref<boolean>(true);
const isSearchingUser = ref<boolean>(false);
const searchUser = ref<string>('');

const selectedUser = ref<UserImpactItem | undefined>(undefined);
const showUserInfoModal = ref<boolean>(false);
const topAgents = ref<AgentImpactItem[]>([]);
const agentPage = ref<number>(1);
const hasMoreAgents = ref<boolean>(true);
const loadingMoreAgents = ref<boolean>(false);
const agentsPageSize = 10;
const loadingTopAgents = ref<boolean>(false);

onMounted(async () => {
    await loadUsersData();
})

const loadUsersData = async () => {
    try{
        loading.value = true;
        await loadData();
    } catch (error) {
        handleError(error);
    } finally {
        loading.value = false;
    }
}

const loadData = async () => {
    userPage.value = 1;
    const users = await api.getImpactTopUsers(props.fromDate, props.toDate, props.teamId, searchUser.value, pageSize + 1, 0);
    topUsers.value = users.slice(0, pageSize);

    hasMoreUsers.value = users.length === pageSize + 1;
    isSearchingUser.value = false;
}

const handleLoadMoreUsers = async () => {
    try {
        loadingMoreUsers.value = true;
        userPage.value++;
        const moreUsers = await api.getImpactTopUsers(props.fromDate, props.toDate, props.teamId, searchUser.value, pageSize + 1, (userPage.value - 1) * pageSize);
        topUsers.value = [...topUsers.value, ...moreUsers.slice(0, pageSize)];
        hasMoreUsers.value = moreUsers.length === pageSize + 1;
    } catch (error) {
        handleError(error);
    } finally {
        loadingMoreUsers.value = false;
    }
}

watch(() => searchUser.value, async () => {
    isSearchingUser.value = true;
    performDebouncedUserSearch();
});

const performDebouncedUserSearch = useDebounce(loadData);

const calculateImpactRatio = (minutesSaved: number, monthlyHours: number):number => {
    return parseFloat(((minutesSaved / 60 + monthlyHours) / monthlyHours).toFixed(2));
}

watch(() => props.teamId, async () => {
    await loadUsersData();
});

const loadUserTopAgents = async (userId: number) => {
    try {
        loadingTopAgents.value = true;
        agentPage.value = 1;
        const agents = await api.getImpactTopAgents(t('privateAgents'), props.fromDate, props.toDate, props.teamId, undefined, agentsPageSize + 1, 0, userId);
        topAgents.value = agents.slice(0, agentsPageSize);
        hasMoreAgents.value = agents.length === agentsPageSize + 1;
    } catch (error) {
        handleError(error);
        topAgents.value = [];
    } finally {
        loadingTopAgents.value = false;
    }
};

const handleLoadMoreAgents = async () => {
    try {
        loadingMoreAgents.value = true;
        agentPage.value++;
        const moreAgents = await api.getImpactTopAgents(t('privateAgents'), props.fromDate, props.toDate, props.teamId, undefined, agentsPageSize + 1, (agentPage.value - 1) * agentsPageSize, selectedUser.value?.userId);
        topAgents.value = [
          ...topAgents.value,
          ...moreAgents.slice(0, agentsPageSize)
        ];
        hasMoreAgents.value = moreAgents.length === agentsPageSize + 1;
    } catch (error) {
        handleError(error);
    } finally {
        loadingMoreAgents.value = false;
    }
};

const showUserInfo = async (user: UserImpactItem) => {
    selectedUser.value = user;
    showUserInfoModal.value = true;
    await loadUserTopAgents(user.userId);
}

</script>

<template>
    <div v-if="loading" class="w-full h-full">
        <div class="bg-pale rounded-lg p-4 animate-pulse">
            <div class="h-5 bg-auxiliar-gray rounded w-32 mb-6"></div>
            <div class="space-y-4">
                <div v-for="i in pageSize" :key="i" class="flex justify-between items-center py-2">
                    <div class="h-4 bg-auxiliar-gray rounded w-32"></div>
                    <div class="h-4 bg-auxiliar-gray rounded w-16"></div>
                </div>
            </div>
        </div>
    </div>
    <DashboardCard v-else :title="t('usersTitle')">
        <template #actions>
            <div class="flex flex-grow justify-end items-center gap-4">
                <InteractiveInput v-model="searchUser" :placeholder="t('searchUser')" start-icon="IconSearch" :loading="isSearchingUser" />
            </div>
        </template>
        <DataTable :value="topUsers" size="small" :show-headers="false">
            <Column field="userName">
                <template #body="slotProps">
                    <div class="flex items-center gap-1 h-8">
                        <span>{{ slotProps.data.userName }}</span>
                    </div>
                </template>
            </Column>
            <Column field="impactRatio" class="w-15 text-center">
                <template #body="slotProps">
                    <div class="flex items-center gap-1 h-8">
                        <DashboardTableDataComparisonCell
                            :current-value="calculateImpactRatio(slotProps.data.minutesSaved, slotProps.data.monthlyHours)"
                            :previous-value="calculateImpactRatio(slotProps.data.previousMinutesSaved, slotProps.data.monthlyHours)"
                            :value-tooltip="t('IAImpactTooltip', { aiHours: (slotProps.data.minutesSaved / 60).toFixed(), humanHours: slotProps.data.monthlyHours.toFixed(2) })"
                            unit="x"
                            :number-decimals="2"
                            icon="IconBoltFilled"
                            iconClass="text-primary"
                        />
                    </div>
                </template>
            </Column>
            <Column field="" class="w-10">
                <template #body="slotProps">
                    <div class="flex items-center gap-2 h-8 justify-end">
                        <SimpleButton shape="square" size="small" variant="secondary" @click="showUserInfo(slotProps.data)" v-tooltip.bottom="t('viewDetailsTooltip')">
                            <IconInfoCircle size="24" />
                        </SimpleButton>
                    </div>
                </template>
            </Column>
            <template #empty>
                <div class="p-4 text-center text-content-muted">
                    {{ t('noUsersFound') }}
                </div>
            </template>
        </DataTable>
        <template #footer>
            <SimpleButton v-if="hasMoreUsers" :disabled="loadingMoreUsers" @click="handleLoadMoreUsers" shape="rounded" shadow="gradient">
                <span v-if="loadingMoreUsers">{{ t('loadingMoreUsers') }}</span>
                <span v-else>{{ t('loadMoreUsers') }}</span>
            </SimpleButton>
        </template>
    </DashboardCard>
    <DashboardCardRecordDialog  v-if="showUserInfoModal"
        :show-modal="showUserInfoModal" 
        :title="selectedUser?.userName || ''" 
        :has-more-data="hasMoreAgents" 
        :loading-more-data="loadingMoreAgents" 
        :is-loading="loadingTopAgents"
        @close="showUserInfoModal = false" 
        @load-more-data="handleLoadMoreAgents">
            <template #summary>
                <div class="flex items-center gap-1 pr-4 border-r-1 border-auxiliar-gray" >
                    <DashboardTableDataComparisonCell 
                        :previous-value="selectedUser!.previousMinutesSaved /60" 
                        :current-value="selectedUser!.minutesSaved /60" 
                        :value-tooltip="t('savedHoursTooltip')" 
                        icon="IconClock" 
                        :number-decimals="2" 
                        :compact-number="true" 
                    />
                </div>
                <div class="flex items-center gap-1" >
                    <DashboardTableDataComparisonCell 
                        :current-value="calculateImpactRatio(selectedUser!.minutesSaved, selectedUser!.monthlyHours)"
                        :previous-value="calculateImpactRatio(selectedUser!.previousMinutesSaved, selectedUser!.monthlyHours)"
                        :value-tooltip="t('IAImpactTooltip', { aiHours: (selectedUser!.minutesSaved / 60).toFixed(), humanHours: selectedUser!.monthlyHours.toFixed(2) })"
                        unit="x" 
                        :number-decimals="2" 
                        icon="IconBoltFilled" 
                        icon-class="text-primary"
                    />
                </div>
            </template>
            <template #details>
                <span class="text-md font-medium">{{ t('agentsTitle') }}</span>
                <DataTable :value="topAgents" size="small" :show-headers="false" class="max-h-[369px] overflow-y-auto" >
                    <Column field="agentName">
                        <template #body="slotProps">
                            <div class="flex items-center gap-2" v-tooltip.top="slotProps.data.authorName ? `${t('author')}: ${slotProps.data.authorName}` : ''">
                                <div class="flex-shrink-0 flex items-center relative">
                                    <AgentAvatar  v-if="!slotProps.data.isExternalAgent" :agent="slotProps.data" :show-shared-status="true" />
                                    <DashboardExternalAgentAvatar v-else :external-agent="slotProps.data" :bordered="true" />
                                </div>
                                {{ slotProps.data.agentName }}
                            </div>
                        </template>
                    </Column>
                    <Column field="minutesSaved" class="w-15">
                        <template #body="slotProps">
                            <div class="flex items-center gap-1">
                                <DashboardTableDataComparisonCell 
                                    :previous-value="slotProps.data.previousMinutesSaved/60" 
                                    :current-value="slotProps.data.minutesSaved/60" 
                                    :value-tooltip="t('savedHoursTooltip')" icon="IconClock" 
                                    :number-decimals="2" 
                                    :compact-number="true"
                                />
                            </div>
                        </template>
                    </Column>
                    <template #empty>
                        <div class="p-4 text-center text-content-muted">
                        {{ t('noAgentsFound') }}
                        </div>
                    </template>
                </DataTable>
            </template>
    </DashboardCardRecordDialog>
</template>

<i18n lang="json">{
    "en": {
        "usersTitle": "Users",
        "loadingMoreUsers": "Loading more users...",
        "loadMoreUsers": "Load more users",
        "searchUser": "Search user",
        "noUsersFound": "No users found",
        "IAImpactTooltip": "Estimated impact factor of the use of AI for this user in the last 30 days ({aiHours} AI hours + {humanHours} Human Hours / {humanHours} Human Hours)",
        "teamOwner": "Leader",
        "teamMember": "Member",
        "author": "Created by",
        "noAgentsFound": "No agents found",
        "agentsTitle": "Agents",
        "privateAgents": "Private agents",
        "savedHoursTooltip": "Total estimated hours saved in the last 30 days",
        "viewDetailsTooltip": "View details"
    },
    "es": {
        "usersTitle": "Usuarios",
        "loadingMoreUsers": "Cargando más usuarios...",
        "loadMoreUsers": "Cargar más usuarios",
        "searchUser": "Buscar usuario",
        "noUsersFound": "No se encontraron usuarios",
        "IAImpactTooltip": "Factor de impacto estimado del uso de IA para este usuario en los últimos 30 días ({aiHours} horas de IA + {humanHours} horas humanas / {humanHours} horas humanas)",
        "teamOwner": "Líder",
        "teamMember": "Miembro",
        "author": "Creado por",
        "noAgentsFound": "No se encontraron agentes",
        "agentsTitle": "Agentes",
        "privateAgents": "Agentes privados",
        "savedHoursTooltip": "Horas totales estimadas ahorradas en los últimos 30 días",
        "viewDetailsTooltip": "Ver detalles"
    }
}</i18n>