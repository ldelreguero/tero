import { computed, ref } from 'vue'
import hljsLight from 'highlight.js/styles/stackoverflow-light.css?url'
import hljsDark from 'highlight.js/styles/stackoverflow-dark.css?url'

export enum UiTheme {
  LIGHT = 'light',
  DARK = 'dark',
}

const STORAGE_KEY = 'tero.ui.theme'
const HLJS_LINK_ID = 'hljs-theme'

function readInitialTheme(): UiTheme {
  const value = localStorage.getItem(STORAGE_KEY)
  if (value === UiTheme.DARK || value === UiTheme.LIGHT) {
    return value
  }
  return getSystemTheme()
}

function getSystemTheme(): UiTheme {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? UiTheme.DARK : UiTheme.LIGHT
}

function applyHighlightTheme(theme: UiTheme) {
  const href = theme === UiTheme.DARK ? hljsDark : hljsLight

  let link = document.getElementById(HLJS_LINK_ID) as HTMLLinkElement | null
  if (!link) {
    link = document.createElement('link')
    link.id = HLJS_LINK_ID
    link.rel = 'stylesheet'
    document.head.appendChild(link)
  }
  link.href = href
}

function applyThemeToDom(theme: UiTheme) {
  const root = document.documentElement
  root.classList.toggle('dark', theme === UiTheme.DARK)
  root.style.colorScheme = theme
  applyHighlightTheme(theme)
}

const themeRef = ref<UiTheme>(readInitialTheme())
applyThemeToDom(themeRef.value)

export function useTheme() {
  const theme = computed(() => themeRef.value)

  const setTheme = (nextTheme: UiTheme) => {
    themeRef.value = nextTheme
    applyThemeToDom(nextTheme)
    localStorage.setItem(STORAGE_KEY, nextTheme)
  }

  const toggleTheme = () => {
    setTheme(themeRef.value === UiTheme.DARK ? UiTheme.LIGHT : UiTheme.DARK)
  }

  return { theme, setTheme, toggleTheme }
}
