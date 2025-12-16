import { computed, ref } from 'vue'

export type UiTheme = 'light' | 'dark'

const STORAGE_KEY = 'tero.ui.theme'

const themeRef = ref<UiTheme>(readInitialTheme())

function readInitialTheme(): UiTheme {
  try {
    const value = localStorage.getItem(STORAGE_KEY)
    return value === 'dark' ? 'dark' : 'light'
  } catch {
    return 'light'
  }
}

function applyThemeToDom(theme: UiTheme) {
  const root = document.documentElement
  root.classList.toggle('dark', theme === 'dark')
  root.style.colorScheme = theme
}

export function useTheme() {
  const theme = computed(() => themeRef.value)
  const isDark = computed(() => themeRef.value === 'dark')

  const setTheme = (nextTheme: UiTheme) => {
    themeRef.value = nextTheme
    applyThemeToDom(nextTheme)
    try {
      localStorage.setItem(STORAGE_KEY, nextTheme)
    } catch {
      // ignore persistence errors
    }
  }

  const toggleTheme = () => {
    setTheme(themeRef.value === 'dark' ? 'light' : 'dark')
  }

  return { theme, isDark, setTheme, toggleTheme }
}
