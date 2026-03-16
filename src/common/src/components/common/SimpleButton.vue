<script setup lang="ts">
const { variant = 'default', size = 'default', type = 'button', shape = 'pill', disabled = false, shadow = null } = defineProps<{
  variant?: 'primary' | 'secondary'  | 'error' | 'light' | 'muted'
  size?: 'default' | 'small' | 'large'
  type?: 'button' | 'submit' | 'reset'
  shape?: 'pill' | 'square' | 'rounded'
  disabled?: boolean,
  shadow?: 'gradient' | 'medium'
}>()

const basePrimaryClasses = 'border-none flex items-center justify-center !ng-offset-0 active:!ring-0 gap-1' + (disabled ? '' : ' hover:!border-none focus:!ring-0 focus:!outline-none focus:!shadow-none');
const defaultStyles = basePrimaryClasses + ' bg-surface text-content !outline-1 !outline-auxiliar-gray shadow-light !ring-1 focus:!ring-1 !ring-auxiliar-gray dark:bg-surface-muted' + (disabled ? '' : ' hover:bg-abstracta hover:text-white');
</script>

<template>
  <button
    :type="type"
    class="transition-colors"
    :disabled="disabled"
    :class="{
      [defaultStyles]: variant === 'default',
      [basePrimaryClasses + ' bg-abstracta text-white' + (disabled ? '' : ' hover:brightness-130')]: variant === 'primary',
      ['bg-surface-muted text-content-muted dark:text-content' + (disabled ? '' : ' hover:contrast-95')]: variant === 'secondary',
      ['bg-error-alt text-white' + (disabled ? '' : ' hover:brightness-105')]: variant === 'error',
      [basePrimaryClasses + ' bg-surface']: variant === 'light',
      [basePrimaryClasses + ' bg-surface-muted']: variant === 'muted',
      ['!bg-surface-muted !text-content-muted' + (disabled ? '' : ' hover:contrast-90')]: disabled,
      'p-2': size === 'default',
      'p-1': size === 'small',
      'w-full p-2': size === 'large',
      'rounded-[9999px]': shape === 'pill', // Hack: Safari doesn't fully support rounded-full, so we use a large value
      'rounded-lg': shape === 'square',
      'rounded-2xl': shape === 'rounded',
      'shadow-gradient-surface': shadow === 'gradient',
      'shadow-md': shadow === 'medium'
    }">
    <slot />
  </button>
</template>