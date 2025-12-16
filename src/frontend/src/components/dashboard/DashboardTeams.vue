<script lang="ts" setup>
import { onMounted, ref, reactive, watch } from 'vue';
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router';
import { IconDeviceFloppy, IconX } from '@tabler/icons-vue';
import {User as OidcUser } from 'oidc-client-ts'
import { useErrorHandler } from '@/composables/useErrorHandler';
import type UsersForm from '@/components/user/UsersForm.vue';
import { NewUserRow } from '@/components/user/UsersForm.vue';
import { ApiService, TeamCreate, Team, User, TeamUpdate, Role, GLOBAL_TEAM_ID } from '@/services/api';
import auth from '@/services/auth';
import { useDateRange } from '@/composables/useDateRange';
import { AnimationEffect } from '@tero/common/utils/animations.js';

const NAME_MAX_LENGTH = 30;
const router = useRouter();
const { t } = useI18n();
const api = new ApiService();
const { handleError } = useErrorHandler();
const loading = ref<boolean>(false);
const teams = ref<Team[]>([]);
const showModal = ref<boolean>(false);
const editingTeam = ref<Team | null>(null);
const deletingTeam = ref<Team | null>(null);
const showDeleteConfirmation = ref<boolean>(false);
const showCloseConfirmation = ref<boolean>(false);
const team = reactive({
  name: editingTeam.value?.name || "",
});
const originalTeam = reactive({
  name: "",
});

const teamUsersEdit = ref<User[]>([]);
const loadingUsers = ref<boolean>(false);
const usersFormRef = ref<InstanceType<typeof UsersForm> | null>(null);
const users = ref<User[]>([]);
const currentUser = ref<OidcUser | null>(null);
const teamUsers = ref<User[]>([])
const newUsers = ref<NewUserRow[]>([new NewUserRow('', Role.TEAM_MEMBER)]);
const isSaving = ref<boolean>(false);

const { fromDate, toDate } = useDateRange()

onMounted(async () => {
  await loadTeams();
  await loadUsers();
})

const loadUsers = async () => {
  try {
    users.value = await api.findUsers();
  } catch (error) {
    handleError(error);
  }
}

const loadTeamUsers = async (teamId: number) => {
  try {
    loadingUsers.value = true;
    teamUsersEdit.value = await api.findTeamUsers(teamId);
  } catch (error) {
    handleError(error);
  } finally {
    loadingUsers.value = false;
  }
}

const loadTeams = async () => {
  loading.value = true;
  try {
    const allTeams = await api.findTeams();
    const global = allTeams.find(t => t.id === GLOBAL_TEAM_ID);
    teams.value = global ? [global, ...allTeams.filter(t => t.id !== GLOBAL_TEAM_ID)]: allTeams;
  } catch (error) {
    router.push('/console')
    handleError(error);
  } finally {
    loading.value = false;
  }
}

const isModified = () => {
  const nameChanged = team.name !== originalTeam.name;
  const hasUsersAdded = !editingTeam.value && newUsers.value.some(user =>
    user.username &&
    user.username.trim() !== '' &&
    user.username !== currentUser.value?.profile?.email
  );
  return nameChanged || hasUsersAdded;
};

const onEditTeam = async (teamId: number) => {
  editingTeam.value = teams.value.find(team => team.id === teamId) || null;
  team.name = editingTeam.value?.name || "";
  originalTeam.name = editingTeam.value?.name || "";
  await loadTeamUsers(teamId);
  showModal.value = true;
}

const onConfirmDeleteTeam = (teamId: number) => {
  showDeleteConfirmation.value = true;
  deletingTeam.value = teams.value.find(team => team.id === teamId) || null;
}

const onCloseModal = () => {
  if (isModified()) {
    showCloseConfirmation.value = true;
  } else {
    closeModal();
  }
}

const closeModal = () => {
  showModal.value = false;
  team.name = "";
  originalTeam.name = "";
  teamUsersEdit.value = [];
  editingTeam.value = null;
}

const handleConfirmClose = () => {
  showCloseConfirmation.value = false;
  closeModal();
}

const handleCancelClose = () => {
  showCloseConfirmation.value = false;
}

const onDeleteTeam = async () => {
  try {
    await api.deleteTeam(deletingTeam?.value?.id!);
    teams.value = teams.value.filter((team) => team.id !== deletingTeam?.value?.id);
  } catch (error) {
    handleError(error);
  } finally {
    showDeleteConfirmation.value = false;
  }
}

const onCreateTeamModal = async () => {
  currentUser.value = await auth.getUser();
  newUsers.value = [new NewUserRow(currentUser.value?.profile?.email || '', Role.TEAM_OWNER), ...newUsers.value];
  editingTeam.value = null;
  team.name = "";
  originalTeam.name = "";
  showModal.value = true;
}

const onUsersUpdate = async () => {
  if (editingTeam.value) {
    await loadTeamUsers(editingTeam.value.id);
  }
}

const onSaveTeam = async () => {
  if (!team.name || team.name.length > NAME_MAX_LENGTH) return;
  try {
    if (editingTeam.value) {
      isSaving.value = true;
      await api.updateTeam(editingTeam.value?.id!, new TeamUpdate(team.name));
      originalTeam.name = team.name;
    } else {
      await api.createTeam(new TeamCreate(team.name, usersFormRef.value?.filterUsersToAdd() || []));
      closeModal();
    }
  } catch (error) {
    handleError(error);
  } finally {
    if (editingTeam.value) isSaving.value = false;
  }
}

const onBlur = async () => {
  if (editingTeam.value && isModified()) {
    await onSaveTeam();
  }
}


watch(() => showModal.value, async () => {
  if (!showModal.value ) {
    await loadTeams();
  }
})
</script>

<template>
  <div class="flex h-full w-full gap-4 min-h-0 flex-1 translate-y-1 flex-col">
    <Animate :effect="AnimationEffect.SLIDE_IN_RIGHT" class="!w-full h-full">
      <TeamsCard :teams="teams" :loading="loading" @edit-team="onEditTeam" @delete-team="onConfirmDeleteTeam" @create-team="onCreateTeamModal" />
    </Animate>
  </div>
  <Dialog class="w-150" :visible="showModal" :modal="true" :closable="false" :draggable="false" :resizable="false" :close-on-escape="false" :dismissable-mask="false" @update:visible="onCloseModal" @hide="onCloseModal">
      <template #header>
          <div class="flex justify-between items-center w-full border-b border-auxiliar-gray pb-4 sticky top-0 bg-surface z-10">
            <div class="flex flex-row items-center gap-2">
              <h3>{{ editingTeam ? t('editTeam') : t('createTeam') }}</h3>
              <div v-if="isSaving" class="flex flex-row px-2 items-center text-sm text-dark-gray animate-pulse">
                <IconDeviceFloppy  />
                <span class="mt-1 ml-1">{{ t('saving') }}</span>
              </div>
            </div>
            <div class="flex gap-4">
                <SimpleButton @click="onCloseModal"><IconX /></SimpleButton>
            </div>
          </div>
      </template>
      <div class="flex flex-col gap-4">
        <div class="form-field flex flex-col flex-grow gap-2">
          <label for="name">{{ t('name') }}</label>
          <InteractiveInput
            v-model="team.name"
            name="name"
            type="text"
            id="name"
            :placeholder="t('namePlaceholder')"
            :required="true"
            :maxlength="NAME_MAX_LENGTH"
            @blur="onBlur"
            :disabled="editingTeam?.id === GLOBAL_TEAM_ID"
          />
        </div>
      </div>
      <div class="mt-4">
        <DashboardCardUsers v-if="editingTeam" :from-date="fromDate" :to-date="toDate" :team-id="editingTeam.id" @update-users="onUsersUpdate" @is-saving="isSaving = $event" :compact-display="true" />
        <UsersForm v-else v-model:new-users="newUsers" :users="users" :team-users="teamUsers" :loading-users="loadingUsers" ref="usersFormRef" />
      </div>
      <template #footer>
        <div class="flex gap-4 mt-3">
          <SimpleButton v-if="!editingTeam" @click="onSaveTeam" shape="square" variant="primary" :disabled="!team.name || !isModified() || team.name.length > NAME_MAX_LENGTH">
              {{ editingTeam ? t('confirmTeamButton') : t('createTeam') }}
          </SimpleButton>
        </div>
      </template>
  </Dialog>
  <Dialog v-model:visible="showDeleteConfirmation" :header="t('deleteConfirmTitle', { team: deletingTeam?.name })" :modal="true" :draggable="false" :resizable="false" :closable="false" class="max-w-150">
    <div class="flex flex-col gap-5">
      <div class="flex flex-row gap-2 items-start whitespace-pre-line">
        {{ t('deleteConfirmDescription') }}
      </div>
      <div class="flex flex-row gap-2 justify-end">
        <SimpleButton @click="showDeleteConfirmation = false" shape="square" variant="secondary">{{ t('cancelDeleteButton') }}</SimpleButton>
        <SimpleButton @click="onDeleteTeam" variant="error" shape="square">{{ t('deleteConfirmButton') }} </SimpleButton>
      </div>
    </div>
  </Dialog>
  <Dialog v-model:visible="showCloseConfirmation" :header="t('closeConfirmTitle')" :modal="true" :draggable="false" :resizable="false" :closable="false" class="max-w-150">
    <div class="flex flex-col gap-5">
      <div class="flex flex-row gap-2 items-start whitespace-pre-line">
        {{ t('closeConfirmDescription') }}
      </div>
      <div class="flex flex-row gap-2 justify-end">
        <SimpleButton @click="handleCancelClose" shape="square" variant="secondary">{{ t('continueEditButton') }}</SimpleButton>
        <SimpleButton @click="handleConfirmClose" shape="square" variant="error">{{ t('discardChangesButton') }}</SimpleButton>
      </div>
    </div>
  </Dialog>
</template>

<i18n lang="json">{
  "en": {
    "createTeam": "Create",
    "editTeam": "Edit",
    "name": "Name",
    "namePlaceholder": "Enter team name",
    "deleteConfirmTitle": "Delete {team}",
    "deleteConfirmDescription": "All agents in this team will be private and all users will be removed from the team.\n\nAre you sure you want to delete this team? This action cannot be undone.",
    "cancelDeleteButton": "Cancel",
    "deleteConfirmButton": "Delete",
    "confirmTeamButton": "Confirm",
    "closeConfirmTitle": "Discard changes?",
    "closeConfirmDescription": "You have unsaved changes. Are you sure you want to close without saving?",
    "continueEditButton": "Continue editing",
    "discardChangesButton": "Discard changes",
    "saving": "Saving..."
  },
  "es": {
    "createTeam": "Crear",
    "editTeam": "Editar",
    "name": "Nombre",
    "namePlaceholder": "Ingresa el nombre del equipo",
    "deleteConfirmTitle": "Eliminar {team}",
    "deleteConfirmDescription": "Todos los agentes en este equipo se volverán privados y todos los usuarios serán removidos del equipo.\n\n¿Estás seguro de que deseas eliminar este equipo? Esta acción no se puede deshacer.",
    "cancelDeleteButton": "Cancelar",
    "deleteConfirmButton": "Eliminar",
    "confirmTeamButton": "Confirmar",
    "closeConfirmTitle": "¿Descartar cambios?",
    "closeConfirmDescription": "Tienes cambios sin guardar. ¿Estás seguro de que quieres cerrar sin guardar?",
    "continueEditButton": "Continuar editando",
    "discardChangesButton": "Descartar cambios",
    "saving": "Guardando..."
  }
}</i18n>
