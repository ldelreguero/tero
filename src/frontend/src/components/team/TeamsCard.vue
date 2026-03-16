<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import { Team, GLOBAL_TEAM_ID } from '@/services/api';
import TeamMenu from './TeamMenu.vue';
import { useDebounce } from '@/composables/useDebounce';

const props = defineProps<{
  teams: Team[];
  loading: boolean;
}>()

const { t } = useI18n();

const emit = defineEmits<{
  (e: 'editTeam', teamId: number): void;
  (e: 'deleteTeam', teamId: number): void;
  (e: 'createTeam'): void;
}>()

const searchTeam = ref<string>('');
const isSearchingTeam = ref<boolean>(false);
const performDebouncedTeamSearch = useDebounce(() => {
  isSearchingTeam.value = false;
});

watch(() => searchTeam.value, async () => {
  isSearchingTeam.value = true;
  performDebouncedTeamSearch();
});

const onEditTeam = (teamId: number) => {
  emit('editTeam', teamId);
};

const onConfirmDeleteTeam = (teamId: number) => {
  emit('deleteTeam', teamId);
};

const filteredTeams = computed(() => {
  if (!searchTeam.value.trim()) return props.teams;

  const searchTerm = searchTeam.value.toLowerCase().trim();
  return props.teams.filter(team => team.name.toLowerCase().includes(searchTerm));
});
</script>

<template>
    <div class="w-full h-full" v-if="loading">
      <div class="w-full bg-surface-muted rounded-lg p-4 animate-pulse h-full">
        <div class="h-5 bg-auxiliar-gray rounded w-32 mb-4"></div>
        <div>
          <div v-for="i in 10" :key="i" class="flex justify-between items-center py-2">
            <div class="flex items-center gap-2">
              <div class="h-4 bg-auxiliar-gray rounded w-32"></div>
            </div>
            <div class="flex items-center gap-4">
              <div class="h-6 bg-auxiliar-gray rounded w-10"></div>
              <div class="h-6 bg-auxiliar-gray rounded w-6"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <DashboardCard v-else :title="t('teamsTitle')">
      <template #actions>
        <div class="flex flex-grow justify-end items-center gap-4">
          <SimpleButton shape="square" @click="emit('createTeam')"><IconPlus />{{ t('createTeam') }}</SimpleButton>
          <InteractiveInput v-model="searchTeam" :placeholder="t('searchTeam')" start-icon="IconSearch" :loading="isSearchingTeam" class="w-full max-w-1/2" />
        </div>
      </template>
      <DataTable :value="filteredTeams" size="small" :show-headers="false">
        <Column field="name">
            <template #body="slotProps">
                <span class="font-medium">{{ slotProps.data.name }}</span>
            </template>
        </Column>
        <Column class="w-16">
            <template #body="slotProps">
                <div class="w-full flex justify-end items-center gap-2" >
                  <IconPinned v-if="slotProps.data.id === GLOBAL_TEAM_ID" size="20" class="text-content-muted rotate-45" />
                  <TeamMenu
                    :team="slotProps.data"
                    @edit-team="onEditTeam(slotProps.data.id)"
                    @delete-team="onConfirmDeleteTeam(slotProps.data.id)"
                  />
                </div>
            </template>
        </Column>
        <template #empty>
          <div class="p-4 text-center text-content-muted">{{ t('noTeamsFound') }}</div>
        </template>
      </DataTable>
    </DashboardCard>
</template>

<i18n lang="json">{
  "en": {
    "teamsTitle": "Teams",
    "searchTeam": "Search team",
    "noTeamsFound": "No teams found",
    "createTeam": "Create"
  },
  "es": {
    "teamsTitle": "Equipos",
    "searchTeam": "Buscar equipo",
    "noTeamsFound": "No se encontraron equipos",
    "createTeam": "Crear"
  }
}</i18n>
