import { IconBrain, IconQuestionMark, IconWorldWww, IconDeviceDesktopBolt, type Icon } from '@tabler/icons-vue'
import { h, type SVGAttributes } from 'vue'

import mcpIcon from '../assets/images/mcp-icon.svg'
import jiraIcon from '../assets/images/jira-icon.svg'

const iconFromImage = (imageSrc: string): Icon => {
  return (props: SVGAttributes) => {
    const { class: className, ...restProps } = (props ?? {}) as SVGAttributes & { class?: unknown }

    return h('img', {
      src: imageSrc,
      width: 20,
      height: 20,
      class: ['tool-menu-icon', className],
      ...restProps
    })
  }
}

const toolIcons: Record<string, Icon> = {
  docs: IconBrain,
  'mcp-*': iconFromImage(mcpIcon),
  jira: iconFromImage(jiraIcon),
  browser: IconDeviceDesktopBolt,
  web: IconWorldWww
}

export const defaultToolNames: Record<string, string> = {
  docs: 'Docs',
  web: 'Web',
  mcp: 'MCP',
  jira: 'Jira',
  browser: 'Browser'
}

export const defaultToolNamesOrder = Object.values(defaultToolNames)

export const findToolIcon = (toolId: string): Icon => {
  const key = toolId.includes('-') ? toolId.split('-', 1)[0] + '-*' : toolId
  return toolIcons[key] || IconQuestionMark
}

export const buildToolConfigName = (toolId: string): string => {
  const [prefix, suffix] = toolId.split('-', 2)
  return suffix && suffix !== '*' ? suffix : defaultToolNames[prefix] || prefix
}
