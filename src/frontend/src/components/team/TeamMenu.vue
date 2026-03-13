<script setup lang="ts">
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { IconPencil, IconX, IconDots } from '@tabler/icons-vue';
import type { MenuItem } from 'primevue/menuitem';
import { GLOBAL_TEAM_ID, type Team} from '@/services/api';

const { t } = useI18n();
const props = defineProps<{
    team: Team;
}>();
const emit = defineEmits<{
    (e: 'editTeam'): void;
    (e: 'deleteTeam'): void;
}>();
const menu = ref();
const isMenuOpen = ref(false);

const handleCloseMenu = () => {
    isMenuOpen.value = false;
}

const items = ref<MenuItem[]>([
    { label: t('editTeamLabel'), tablerIcon: IconPencil, command: () => { emit('editTeam') } },
    ...(props.team.id !== GLOBAL_TEAM_ID ? [{ label: t('deleteTeamLabel'), tablerIcon: IconX, command: () => { emit('deleteTeam') } }] : [])
]);

const handleMenuToggle = (event: Event) => {
    menu.value.toggle(event);
}
</script>

<template>
    <div>
        <SimpleButton class="rounded-lg" variant="muted" size="small" @click.prevent="handleMenuToggle($event)">
            <IconDots stroke-width="2" :class="isMenuOpen ? 'text-abstracta' : 'text-content-muted'" />
        </SimpleButton>
        <Menu ref="menu" :model="items ?? []" :popup="true" @show="isMenuOpen = true" @hide="handleCloseMenu" @keydown.esc="handleCloseMenu">
            <template #item="{ item }">
                <MenuItemTemplate :item="item"/>
            </template>
        </Menu>
    </div>
</template>
<i18n lang="json">
{
    "en": {
        "editTeamLabel": "Edit team",
        "deleteTeamLabel": "Delete team"
    },
    "es": {
        "editTeamLabel": "Editar equipo",
        "deleteTeamLabel": "Eliminar equipo"
    }
}
</i18n>
