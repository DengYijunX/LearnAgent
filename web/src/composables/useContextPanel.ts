import { computed, onMounted, onUnmounted, ref } from 'vue'

const OPEN_KEY = 'learnagent.context-panel.open'
const PIN_KEY = 'learnagent.context-panel.pinned'

export function useContextPanel() {
  const isOpen = ref(false)
  const isPinned = ref(false)
  const isWide = ref(false)
  let media: MediaQueryList | null = null

  function savedBoolean(key: string): boolean | null {
    const value = localStorage.getItem(key)
    return value === null ? null : value === 'true'
  }

  function syncResponsive(event?: MediaQueryListEvent) {
    isWide.value = event?.matches ?? media?.matches ?? false
    const savedOpen = savedBoolean(OPEN_KEY)
    const savedPin = savedBoolean(PIN_KEY)
    isOpen.value = savedOpen ?? isWide.value
    isPinned.value = savedPin ?? isWide.value
  }

  function toggle() {
    isOpen.value = !isOpen.value
    localStorage.setItem(OPEN_KEY, String(isOpen.value))
  }

  function close() {
    isOpen.value = false
    localStorage.setItem(OPEN_KEY, 'false')
  }

  function togglePinned() {
    isPinned.value = !isPinned.value
    if (isPinned.value) isOpen.value = true
    localStorage.setItem(PIN_KEY, String(isPinned.value))
    localStorage.setItem(OPEN_KEY, String(isOpen.value))
  }

  onMounted(() => {
    media = window.matchMedia('(min-width: 1440px)')
    syncResponsive()
    media.addEventListener('change', syncResponsive)
  })

  onUnmounted(() => media?.removeEventListener('change', syncResponsive))

  return {
    isOpen,
    isPinned,
    isWide,
    isOverlay: computed(() => !isWide.value || !isPinned.value),
    toggle,
    close,
    togglePinned
  }
}
