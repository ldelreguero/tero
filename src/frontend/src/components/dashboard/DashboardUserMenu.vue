<script setup lang="ts">
import { GLOBAL_TEAM_ID, type TeamUser, TeamRoleStatus } from '@/services/api';
import { IconPencil, IconX } from '@tabler/icons-vue';
import type { MenuItem } from 'primevue/menuitem';
import { ref, computed } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const props = defineProps<{
    user: TeamUser;
    teamId: number;
}>();
const emit = defineEmits<{
    (e: 'editUserRole'): void;
    (e: 'deleteUser'): void;
}>();
const menu = ref();
const isMenuOpen = ref(false);

const handleCloseMenu = () => {
    isMenuOpen.value = false;
}

const items = computed<MenuItem[]>(() => {
    const menuItems: MenuItem[] = [];
    let removeLabel = t('deleteInvitation');
    if (props.user.roleStatus !== TeamRoleStatus.REJECTED) {
        menuItems.push({ label: t('editRoleLabel'), tablerIcon: IconPencil, command: () => { emit('editUserRole') } });
        removeLabel = t('deleteUserLabel');
    }
    if (props.user.roleStatus === TeamRoleStatus.PENDING || !props.user.verified) {
        removeLabel = t('cancelInvitation');
    }
    if (props.teamId !== GLOBAL_TEAM_ID || !props.user.verified) {
        menuItems.push({ label: removeLabel, tablerIcon: IconX, command: () => { emit('deleteUser') } });
    }
    return menuItems;
});

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
                <MenuItemTemplate :item="item" />
            </template>
        </Menu>
    </div>
</template>
<i18n lang="json">
{
    "en": {
        "editRoleLabel": "Edit role",
        "deleteUserLabel": "Remove from team",
        "deleteInvitation": "Delete invitation",
        "cancelInvitation": "Cancel invitation"
    },
    "es": {
        "editRoleLabel": "Editar rol",
        "deleteUserLabel": "Quitar del equipo",
        "deleteInvitation": "Eliminar invitación",
        "cancelInvitation": "Cancelar invitación"
    }
}
</i18n>