import { nextTick, ref } from 'vue'
import MarkdownIt from 'markdown-it'
import MarkdownItPlantuml from 'markdown-it-plantuml'
import Token from 'markdown-it/lib/token'
import 'highlight.js/styles/stackoverflow-light.css'
import hljs from 'highlight.js'
import { escapeHtml } from 'markdown-it/lib/common/utils'
import copyIcon from '../assets/images/copy-icon.svg?raw'
import csvIcon from '../assets/images/csv-icon.svg?raw'
import { useCodeCopyHandler } from './useCodeCopyHandler'
import moment from 'moment'
import * as echarts from 'echarts'
import * as XLSX from 'xlsx'
import { saveAs } from 'file-saver'

var chart: any
var prevWidth: number = 0

const messageElement = ref<HTMLElement | null>(null)
const CSV_FILENAME = 'table.csv'

const onResize = () => {
  if (messageElement.value!.scrollWidth != prevWidth && chart) {
    prevWidth = messageElement.value!.scrollWidth
    chart.resize()
  }
}

const resizeObserver: ResizeObserver = new ResizeObserver(onResize)

const useTables = (md: MarkdownIt) => {
  const downloadButton = `
    <div class="flex mt-4">
      <button
        class="inline-flex items-center whitespace-nowrap rounded-xl bg-surface border border-auxiliar-gray px-3 py-1.5 gap-1 text-light-gray"
        onclick="downloadTableCSV(this)"
      >
        ${csvIcon} ${CSV_FILENAME}
      </button>
    </div>
  `
  md.core.ruler.after('block', 'table_wrapper', function responsiveTableWrapper(state) {
    const tokens = state.tokens
    // Walk backwards to avoid index shifts
    for (let i = tokens.length - 1; i >= 0; i--) {
      if (tokens[i].type === 'table_close') {
        const wrapClose = new Token('html_block', '', 0)
        wrapClose.content = `</div>${downloadButton}</div>` 
        tokens.splice(i + 1, 0, wrapClose)
      }
      if (tokens[i].type === 'table_open') {
        const wrapOpen = new Token('html_block', '', 0)
        wrapOpen.content = '<div class="flex flex-col gap-2"><div class="overflow-x-auto">'
        tokens.splice(i, 0, wrapOpen)
      }
    }
  })

  md.renderer.rules.td_open = () => '<td class="break-words border border-auxiliar-gray px-4 py-2">'
  md.renderer.rules.th_open = () => '<th class="break-words border border-auxiliar-gray px-4 py-2 bg-pale !font-medium">'
  md.renderer.rules.table_close = () => '</table>'
  md.renderer.rules.tbody_open = () => '<tbody class="divide-y divide-auxiliar-gray">'
}

const useCodeInline = (md: MarkdownIt) => {
  md.renderer.rules.code_inline = (tokens, idx) => {
    return `<code class="bg-pale p-0.5 rounded-md text-sm font-mono">${md.utils.escapeHtml(tokens[idx].content)}</code>`
  }
}

const useTargetBlankLinks = (md: MarkdownIt) => {
  let defaultRender =
    md.renderer.rules.link_open ||
    function (tokens, idx, options, env, self) {
      return self.renderToken(tokens, idx, options)
    }
  md.renderer.rules.link_open = function (tokens, idx, options, env, self) {
    tokens[idx].attrSet('target', '_blank')
    tokens[idx].attrJoin('class', '!inline px-1')
    return defaultRender(tokens, idx, options, env, self)
  }
}

const listDecimalPlugin = (md: MarkdownIt): void => {
  const defaultRender = md.renderer.rules.ordered_list_open || ((tokens, idx, options, env, self) => self.renderToken(tokens, idx, options))

  md.renderer.rules.ordered_list_open = (tokens, idx, options, env, self) => {
    tokens[idx].attrJoin('class', 'list-decimal pl-6')
    return defaultRender(tokens, idx, options, env, self)
  }
}

const listBulletPlugin = (md: MarkdownIt): void => {
  const defaultRender = md.renderer.rules.bullet_list_open || ((tokens, idx, options, env, self) => self.renderToken(tokens, idx, options))

  md.renderer.rules.bullet_list_open = (tokens, idx, options, env, self) => {
    tokens[idx].attrJoin('class', 'list-disc pl-2')
    return defaultRender(tokens, idx, options, env, self)
  }
}

const blockquotePlugin = (md: MarkdownIt): void => {
  md.renderer.rules.blockquote_open = () => {
    return `<blockquote class="flex gap-3 my-2 px-6 py-4 border-l-8 border-pale">`
  }

  md.renderer.rules.blockquote_close = () => {
    return `</blockquote>`
  }
}

const useEcharts = (md: MarkdownIt) => {
  const defaultRender =
    md.renderer.rules.fence ||
    function (tokens, idx, options, env, self) {
      return self.renderToken(tokens, idx, options)
    }

  md.renderer.rules.fence = function (tokens, idx, options, env, self) {
    const token = tokens[idx]
    const code = token.content.trim()
    if (token.info === 'echarts') {
      nextTick().then(() => {
        const container = messageElement.value!
        const chartDiv = container.querySelector('.echarts')
        const chartData = container.querySelector('.echarts-data')
        if (chartDiv && chartData) {
          chart = echarts.init(chartDiv as HTMLDivElement)
          const options = JSON.parse(chartData.textContent || '')
          if (options.xAxis?.axisLabel) solveEchartsFormatter(options.xAxis.axisLabel)
          if (options.xAxis?.axisPointer?.label) solveEchartsFormatter(options.xAxis.axisPointer.label)
          chart.setOption(options)
        }
      })
      return `<div class="echarts" style="width: 100%; height: 200px;"></div><div class="echarts-data" style='display:none'>${code}</div>`
    }
    return defaultRender(tokens, idx, options, env, self)
  }
}

const solveEchartsFormatter = (obj: any) => {
  if (obj && obj.formatter) {
    if (obj.formatter.name === 'formatEpoch') {
      obj.formatter = formatEpoch(obj.formatter)
    }
  }
}

const formatEpoch = (config: any): ((value: any) => string) => {
  return (value: any) => {
    if (typeof value === 'object') {
      value = value.value
    }
    const time = moment(parseInt(value))
    return time.format(config.format)
  }
}

export const renderMarkDown = (text: string, isComplete: boolean, t?: (key: string) => string) => {
  let md = new MarkdownIt({
    highlight: function (str, lang) {
      if (lang) {
        const copyButtonText = t ? t('copyCodeButton') : 'Copy'
        let code = `<pre class="b-1 my-3">
        <div class="flex items-center justify-between p-2 bg-pale border-t border-l border-r border-auxiliar-gray rounded-t-lg">
          <span class="text-xs lowercase text-dark-gray font-[sora]">${lang}</span>
          <button class="copy-code-btn flex items-center text-xs text-dark-gray hover:text-dark transition">
            ${copyIcon}
            <span class="font-[sora]">${copyButtonText}</span>
          </button>
        </div>
        <code class="block p-2 bg-surface-muted border border-auxiliar-gray rounded-b-lg overflow-x-auto">`.replace(/  |\r\n|\n|\r/gm, '')
        if (hljs.getLanguage(lang)) {
          try {
            code += hljs.highlight(str, { language: lang }).value
          } catch (__) {}
        } else {
          code += escapeHtml(str)
        }
        code += '</code></pre>'
        return code
      }
      return ''
    }
  })
  useTargetBlankLinks(md)
  useEcharts(md)
  useCodeInline(md)
  if (isComplete) md.use(MarkdownItPlantuml)
  md.use(useTables)
  md.use(listDecimalPlugin)
  md.use(listBulletPlugin)
  md.use(blockquotePlugin)
  return md.render(text)
}

export const initializeResizeObserver = (element: HTMLElement | null): (() => void) => {
  messageElement.value = element
  if (messageElement.value) resizeObserver.observe(messageElement.value)
  return () => {
    if (messageElement.value) resizeObserver.unobserve(messageElement.value)
    messageElement.value = null
  }
}

export const initializeCodeCopyHandler = (t?: (key: string) => string): void => {
  if (t) useCodeCopyHandler(t)
}

export function downloadTableCSV(button: HTMLElement) {
  const table = button.parentElement?.previousElementSibling?.querySelector('table')
  if (!table) return

  const workbook = XLSX.utils.table_to_book(table, { raw: true })
  const wbout = XLSX.write(workbook, { bookType: 'csv', type: 'array' })
  saveAs(new Blob([wbout], { type: 'text/csv;charset=utf-8;' }), CSV_FILENAME)
}

if (typeof window !== 'undefined') {
  ;(window as any).downloadTableCSV = downloadTableCSV
}
