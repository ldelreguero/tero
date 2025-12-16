<script lang="ts" setup>
import MarkdownIt from 'markdown-it'

const md = MarkdownIt({})
defineProps({ message: String })

const addTargetBlankToLinks = (md: MarkdownIt) => {
  const defaultRender = md.renderer.rules.link_open || function (tokens, idx, options, env, self) {
    return self.renderToken(tokens, idx, options)
  }
  md.renderer.rules.link_open = function (tokens, idx, options, env, self) {
    tokens[idx].attrSet('target', '_blank')
    return defaultRender(tokens, idx, options, env, self)
  }
}
addTargetBlankToLinks(md)
</script>

<template>
  <div v-html="md.render(message!)" />
</template>

<style>
@import '@/assets/styles.css';

div .Vue-Toastification__container {
  @apply p-2 pt-6;
}

div .Vue-Toastification__toast {
  @apply bg-surface p-2 text-sm text-content font-sans rounded-md align-middle;
}

div .Vue-Toastification__icon {
  @apply text-error mr-2 w-8;
}

div .Vue-Toastification__close-button {
  @apply text-content-muted h-fit;
}

div .Vue-Toastification__toast--error .Vue-Toastification__progress-bar {
  @apply bg-error;
}

div .Vue-Toastification__toast--info .Vue-Toastification__progress-bar {
  @apply bg-info;
}
</style>
