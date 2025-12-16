import { IconBrain, IconQuestionMark, IconWorldWww, IconDeviceDesktopBolt, type Icon } from '@tabler/icons-vue'
import mcpIcon from '@/assets/images/mcp-icon.svg'
import jiraIcon from '@/assets/images/jira-icon.svg'
import { h, type SVGAttributes } from 'vue'

const iconFromImage = (imageSrc: string, toolIcon: string): Icon => {
  return (props: SVGAttributes) => {
    const { class: className, ...restProps } = (props ?? {}) as SVGAttributes & { class?: unknown }

    return h('img', {
      src: imageSrc,
      width: 20,
      height: 20,
      'data-tool-icon': toolIcon,
      class: ['tool-menu-icon', className],
      ...restProps
    })
  }
}

export function useToolConfig() {
  const menuIcons: Record<string, Icon> = {
    docs: IconBrain,
    'mcp-*': iconFromImage(mcpIcon, 'mcp'),
    "jira": iconFromImage(jiraIcon, 'jira'),
    browser: IconDeviceDesktopBolt,
    web: IconWorldWww
  }

  const defaultNames: Record<string, string> = {
    docs: 'Docs',
    mcp: 'MCP',
    jira: 'Jira',
    browser: 'Browser',
    web: 'Web'
  }

  const findToolIcon = (toolId: string) => {
    const key = toolId.includes('-') ? toolId.split('-', 1)[0] + '-*' : toolId
    return menuIcons[key as keyof typeof menuIcons] || IconQuestionMark
  }

  const buildToolConfigName = (toolId: string) => {
    const [prefix, suffix] = toolId.split('-', 2)
    return suffix && suffix !== '*' ? suffix : defaultNames[prefix] || prefix
  }

  return { findToolIcon, buildToolConfigName }
}
