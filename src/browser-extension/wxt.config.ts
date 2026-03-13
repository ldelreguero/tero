import { defineConfig } from 'wxt';
import vue from "@vitejs/plugin-vue";
import vueI18n from '@intlify/unplugin-vue-i18n/vite';
import tailwindcss from "@tailwindcss/vite";
import Components from 'unplugin-vue-components/vite';
import { PrimeVueResolver } from '@primevue/auto-import-resolver'


export default defineConfig({
    outDir: "dist",
    manifest: () => ({
        name: process.env.EXTENSION_NAME || "Tero Browser Copilot",
        version: process.env.EXTENSION_VERSION,
        key: !process.env.EXTENSION_NAME ? "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAxwtmVjfoXy7ZEzolOtTNI8iEyMQq0b+6gL69hTdTDF5udbayzGRFrEz7VHiA8ovqQ9gtCR/NVucBzcItQL5qTPBk80qOSLxylaeF3H4An/7g21/xr8Dvu4ItfpyfnzMSzQFAxlkq3hbx57wQSg9qawtI+ga4D1IzKz86G70EdcKXF/Dic8gkObAmgr3fnI+q1Jtk5AuiPUAtjE5H4c00ZcXGFeSJja5ebSKvJDyGdAK6DiRG6B5rsimrhD8mx0xQppjtlQQ/d+EOYgtMpAnn3Xu44yPJBx9lY19kRi6gPNXtN0vjVvaHv+AcBNayRdpHgEm6Clk8SDPXliozX3zgVwIDAQAB" : undefined,
        web_accessible_resources: [{
            matches: ['http://*/*', 'https://*/*'],
            resources: ['iframe.html']
        }],
        permissions: [
            "activeTab",
            "storage",
            "contextMenus",
            "webRequest",
            "declarativeNetRequest",
            "clipboardWrite",
            "identity",
            "tabs"
        ],
        action: {}
    }),
    webExt: {
        startUrls: [process.env.START_URL || "https://github.com/abstracta/tero"]
    },
    vite: () => ({
        esbuild: {
            supported: {
                'top-level-await': true
            }
        },
        plugins: [
            vue(),
            tailwindcss(),
            Components({
                dts: true,
                dirs: ['components', '../common/src'],
                resolvers: [PrimeVueResolver()]
            }),
            vueI18n({}),
        ],
    }),
});
