<script setup lang="ts">
import { useData, useRoute } from 'vitepress'
import DefaultTheme from 'vitepress/theme'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const Layout = DefaultTheme.Layout
const route = useRoute()
const { frontmatter } = useData()
const MIN_SCALE = 0.6
const MAX_SCALE = 3
const SCALE_STEP = 0.2
const WIDE_MODE_STORAGE_KEY = 'kb-wide-mode'

let renderToken = 0
let themeObserver: MutationObserver | null = null
let fullscreenChangeHandler: (() => void) | null = null
const isWideMode = ref(false)
const showWideModeToggle = computed(() => frontmatter.value.layout !== 'home')

function clampScale(scale: number) {
  return Math.min(MAX_SCALE, Math.max(MIN_SCALE, Math.round(scale * 10) / 10))
}

function refreshDiagramLayouts() {
  const blocks = document.querySelectorAll<HTMLElement>('.kb-mermaid-block')
  for (const block of blocks) {
    updateFullscreenLabel(block)
    applyMermaidScale(block, Number(block.dataset.mermaidScale || '1'))
  }
}

function applyWideModeState() {
  if (typeof document === 'undefined') {
    return
  }

  document.documentElement.classList.toggle('kb-wide-mode', isWideMode.value)
  window.requestAnimationFrame(() => {
    refreshDiagramLayouts()
  })
}

function toggleWideMode() {
  isWideMode.value = !isWideMode.value
}

function updateFullscreenLabel(block: HTMLElement) {
  const button = block.querySelector<HTMLButtonElement>('[data-mermaid-action="fullscreen"]')
  if (!button) {
    return
  }
  button.textContent = document.fullscreenElement === block ? '退出全屏' : '最大化'
}

function applyMermaidScale(block: HTMLElement, scale: number) {
  const canvas = block.querySelector<HTMLElement>('.kb-mermaid-canvas')
  const render = block.querySelector<HTMLElement>('.kb-mermaid-render')
  const badge = block.querySelector<HTMLElement>('.kb-mermaid-scale')
  const viewport = block.querySelector<HTMLElement>('.kb-mermaid-viewport')
  const baseWidth = Number(block.dataset.mermaidBaseWidth || 0)
  const baseHeight = Number(block.dataset.mermaidBaseHeight || 0)

  if (!canvas || !render || !badge || !viewport || !baseWidth || !baseHeight) {
    return
  }

  const nextScale = clampScale(scale)
  const scaledWidth = Math.max(Math.round(baseWidth * nextScale), viewport.clientWidth - 16, 320)
  const scaledHeight = Math.max(Math.round(baseHeight * nextScale), 240)

  block.dataset.mermaidScale = nextScale.toFixed(1)
  canvas.style.width = `${scaledWidth}px`
  canvas.style.height = `${scaledHeight}px`
  render.style.transform = `scale(${nextScale})`
  badge.textContent = `${Math.round(nextScale * 100)}%`
}

function setupRenderedMermaidBlock(block: HTMLElement) {
  const render = block.querySelector<HTMLElement>('.kb-mermaid-render')
  const viewport = block.querySelector<HTMLElement>('.kb-mermaid-viewport')
  const svg = render?.querySelector<SVGSVGElement>('svg')

  if (!render || !viewport || !svg) {
    return
  }

  const viewBox = svg.viewBox.baseVal
  const width = Math.ceil(viewBox?.width || svg.getBoundingClientRect().width || render.scrollWidth)
  const height = Math.ceil(viewBox?.height || svg.getBoundingClientRect().height || render.scrollHeight)
  if (!width || !height) {
    return
  }

  block.dataset.mermaidBaseWidth = String(width)
  block.dataset.mermaidBaseHeight = String(height)
  render.style.width = `${width}px`
  render.style.height = `${height}px`
  svg.style.width = `${width}px`
  svg.style.height = `${height}px`

  applyMermaidScale(block, Number(block.dataset.mermaidScale || '1'))
  updateFullscreenLabel(block)
}

function handleMermaidToolbarClick(event: MouseEvent) {
  const target = event.target as HTMLElement | null
  const button = target?.closest<HTMLButtonElement>('[data-mermaid-action]')
  if (!button) {
    return
  }

  const block = button.closest<HTMLElement>('.kb-mermaid-block')
  if (!block) {
    return
  }

  const action = button.dataset.mermaidAction
  const currentScale = Number(block.dataset.mermaidScale || '1')

  if (action === 'zoom-in') {
    applyMermaidScale(block, currentScale + SCALE_STEP)
    return
  }

  if (action === 'zoom-out') {
    applyMermaidScale(block, currentScale - SCALE_STEP)
    return
  }

  if (action === 'reset') {
    applyMermaidScale(block, 1)
    return
  }

  if (action === 'fullscreen') {
    if (document.fullscreenElement === block) {
      void document.exitFullscreen()
    } else {
      void block.requestFullscreen()
    }
  }
}

async function renderMermaidDiagrams() {
  if (typeof window === 'undefined') {
    return
  }

  const currentToken = ++renderToken
  await nextTick()

  const mermaidBlocks = Array.from(
    document.querySelectorAll<HTMLElement>('.vp-doc div.language-mermaid'),
  )
  if (!mermaidBlocks.length) {
    return
  }

  const mermaidModule = await import('mermaid')
  if (currentToken !== renderToken) {
    return
  }

  const mermaid = mermaidModule.default
  mermaid.initialize({
    startOnLoad: false,
    securityLevel: 'loose',
    theme: document.documentElement.classList.contains('dark') ? 'dark' : 'neutral',
    fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
  })

  const nodes: HTMLElement[] = []

  for (const block of mermaidBlocks) {
    const source =
      block.dataset.mermaidSource ??
      block.querySelector('pre code')?.textContent?.trim() ??
      ''
    if (!source) {
      continue
    }

    block.dataset.mermaidSource = source
    block.classList.remove('line-numbers-mode', 'vp-adaptive-theme')
    block.classList.add('kb-mermaid-block')
    block.dataset.mermaidScale = '1'

    const toolbar = document.createElement('div')
    toolbar.className = 'kb-mermaid-toolbar'
    toolbar.innerHTML = `
      <button type="button" class="kb-mermaid-action" data-mermaid-action="zoom-out" aria-label="缩小图表">-</button>
      <span class="kb-mermaid-scale">100%</span>
      <button type="button" class="kb-mermaid-action" data-mermaid-action="zoom-in" aria-label="放大图表">+</button>
      <button type="button" class="kb-mermaid-action kb-mermaid-action-text" data-mermaid-action="reset">重置</button>
      <button type="button" class="kb-mermaid-action kb-mermaid-action-text" data-mermaid-action="fullscreen">最大化</button>
    `

    const viewport = document.createElement('div')
    viewport.className = 'kb-mermaid-viewport'

    const canvas = document.createElement('div')
    canvas.className = 'kb-mermaid-canvas'

    const host = document.createElement('div')
    host.className = 'kb-mermaid-render mermaid'
    host.textContent = source

    canvas.append(host)
    viewport.append(canvas)
    block.replaceChildren(toolbar, viewport)
    nodes.push(host)
  }

  if (nodes.length) {
    await mermaid.run({
      nodes,
      suppressErrors: true,
    })
  }

  await new Promise<void>((resolve) => {
    window.requestAnimationFrame(() => resolve())
  })
  for (const block of mermaidBlocks) {
    setupRenderedMermaidBlock(block)
  }
}

onMounted(() => {
  isWideMode.value = window.localStorage.getItem(WIDE_MODE_STORAGE_KEY) === 'true'
  applyWideModeState()
  void renderMermaidDiagrams()
  document.addEventListener('click', handleMermaidToolbarClick)

  fullscreenChangeHandler = () => {
    refreshDiagramLayouts()
  }
  document.addEventListener('fullscreenchange', fullscreenChangeHandler)

  themeObserver = new MutationObserver(() => {
    void renderMermaidDiagrams()
  })
  themeObserver.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['class'],
  })
})

watch(
  () => route.path,
  () => {
    applyWideModeState()
    void renderMermaidDiagrams()
  },
)

watch(isWideMode, (value) => {
  if (typeof window === 'undefined') {
    return
  }

  window.localStorage.setItem(WIDE_MODE_STORAGE_KEY, value ? 'true' : 'false')
  applyWideModeState()
})

onBeforeUnmount(() => {
  themeObserver?.disconnect()
  themeObserver = null
  document.removeEventListener('click', handleMermaidToolbarClick)
  if (fullscreenChangeHandler) {
    document.removeEventListener('fullscreenchange', fullscreenChangeHandler)
    fullscreenChangeHandler = null
  }
})
</script>

<template>
  <Layout>
    <template #doc-before>
      <div v-if="showWideModeToggle" class="kb-doc-toolbar">
        <button type="button" class="kb-doc-toolbar-button" @click="toggleWideMode">
          {{ isWideMode ? '退出宽栏' : '宽栏模式' }}
        </button>
      </div>
    </template>
  </Layout>
</template>
