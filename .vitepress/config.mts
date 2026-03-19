import { defineConfig } from 'vitepress'

const repositoryName = process.env.GITHUB_REPOSITORY?.split('/')[1]
const base = process.env.GITHUB_ACTIONS && repositoryName ? `/${repositoryName}/` : '/'

export default defineConfig({
  base,
  srcDir: 'content',
  title: 'Reports Knowledge Base',
  description: '基于 reports 素材库自动生成的 VitePress 知识网站',

  themeConfig: {
    nav: [
      { text: '首页', link: '/' },
      { text: '分类体系', link: '/taxonomy/' },
      { text: '时间轴', link: '/timeline/' },
      { text: '知识图谱', link: '/graph/' },
      { text: '优先级', link: '/priority/' },
      { text: 'AI 与软件', link: '/ai-software/' },
      { text: '市场与财富', link: '/markets-wealth/' },
      { text: '人与生活', link: '/people-life/' },
      { text: '世界与战略', link: '/world-strategy/' },
      { text: '流程与系统', link: '/operations/' },
    ],

    sidebar: {
      '/taxonomy/': [
        {
          text: '导航',
          items: [
            { text: '分类体系', link: '/taxonomy/' },
            { text: '时间轴', link: '/timeline/' },
            { text: '知识图谱', link: '/graph/' },
            { text: '优先级', link: '/priority/' },
          ],
        },
      ],
      '/timeline/': [
        {
          text: '导航',
          items: [
            { text: '时间轴', link: '/timeline/' },
            { text: '知识图谱', link: '/graph/' },
            { text: '优先级', link: '/priority/' },
          ],
        },
      ],
      '/graph/': [
        {
          text: '导航',
          items: [
            { text: '知识图谱', link: '/graph/' },
            { text: '时间轴', link: '/timeline/' },
            { text: '分类体系', link: '/taxonomy/' },
          ],
        },
      ],
      '/priority/': [
        {
          text: '导航',
          items: [
            { text: '优先级', link: '/priority/' },
            { text: '时间轴', link: '/timeline/' },
            { text: '知识图谱', link: '/graph/' },
            { text: '分类体系', link: '/taxonomy/' },
          ],
        },
      ],
      '/ai-software/': [
        {
          text: 'AI 与软件',
          items: [
            { text: '总览', link: '/ai-software/' },
            { text: '代理与工具', link: '/ai-software/agents-tooling/' },
            { text: '模型与研究', link: '/ai-software/models-research/' },
          ],
        },
      ],
      '/markets-wealth/': [
        {
          text: '市场与财富',
          items: [
            { text: '总览', link: '/markets-wealth/' },
            { text: '投资策略', link: '/markets-wealth/investing-strategy/' },
            { text: '财富心理', link: '/markets-wealth/wealth-psychology/' },
          ],
        },
      ],
      '/people-life/': [
        {
          text: '人与生活',
          items: [
            { text: '总览', link: '/people-life/' },
            { text: '关系与信任', link: '/people-life/relationships-trust/' },
            { text: '家庭与成长', link: '/people-life/family-growth/' },
          ],
        },
      ],
      '/world-strategy/': [
        {
          text: '世界与战略',
          items: [
            { text: '总览', link: '/world-strategy/' },
            { text: '战略研究', link: '/world-strategy/strategic-research/' },
            { text: '文化与历史', link: '/world-strategy/culture-history/' },
          ],
        },
      ],
      '/operations/': [
        {
          text: '流程与系统',
          items: [
            { text: '总览', link: '/operations/' },
            { text: '系统与工作流', link: '/operations/systems-workflows/' },
            { text: '抓取异常', link: '/operations/fetch-failures/' },
            { text: '待归类', link: '/operations/review-queue/' },
          ],
        },
      ],
    },

    search: {
      provider: 'local',
    },

    socialLinks: [],
    lastUpdated: true,

    outline: {
      level: [2, 3],
    },
  },

  markdown: {
    lineNumbers: true,
  },
})
