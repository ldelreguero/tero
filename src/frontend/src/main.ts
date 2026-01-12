import { createApp, type Component } from 'vue'
import { createI18n } from 'vue-i18n'
import PrimeVue from 'primevue/config'
import { definePreset } from '@primeuix/themes'
import Aura from '@primeuix/themes/aura'
import Toast from 'vue-toastification'
import 'vue-toastification/dist/index.css'
import { MotionPlugin } from '@vueuse/motion';
import '@/assets/styles.css'
import * as TablerIcons from '@tabler/icons-vue'
import moment from 'moment';

import 'moment/locale/es';
moment.locale('es', {
  monthsShort: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
});

import App from './App.vue'
import router from './router'
import clickOutside from '../../common/src/utils/clickOutside'

const i18n = createI18n({
  legacy: false,
  locale: navigator.language.split('-')[0],
  fallbackLocale: 'en',
  missingWarn: false,
  fallbackWarn: false
})

const app = createApp(App)
const primeTheme = definePreset(Aura)
for (const [name, component] of Object.entries(TablerIcons)) {
  app.component(name, component as Component)
}
app.use(router)
app.use(i18n)
app.use(PrimeVue, {
  theme: {
    preset: primeTheme,
    options: {
      darkModeSelector: 'html.dark',
    }
  }
})
app.use(Toast, {})
app.use(MotionPlugin)
app.directive('click-outside', clickOutside);
app.mount('#app')
