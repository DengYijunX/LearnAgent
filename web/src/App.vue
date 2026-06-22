<script setup lang="ts">
import { ref, onMounted } from 'vue'
import AppSidebar from './components/layout/AppSidebar.vue'
import ChatPanel from './components/chat/ChatPanel.vue'
import { useSessionStore } from './stores/session'

const sessionStore = useSessionStore()
const chatPanelRef = ref<InstanceType<typeof ChatPanel> | null>(null)

onMounted(async () => {
  await sessionStore.loadSessions()
})

function handleSelectSession(id: string) {
  chatPanelRef.value?.selectSession(id)
}

async function handleCreateSession() {
  chatPanelRef.value?.createSession()
}
</script>

<template>
  <div class="app-canvas text-[var(--ink)]">
    <div class="ambient-orb ambient-orb--top" aria-hidden="true" />
    <div class="ambient-orb ambient-orb--bottom" aria-hidden="true" />
    <div class="app-noise" aria-hidden="true" />

    <div class="app-shell">
      <AppSidebar
        @select-session="handleSelectSession"
        @create-session="handleCreateSession"
      />
      <main class="relative flex min-w-0 flex-1 flex-col overflow-hidden">
        <ChatPanel ref="chatPanelRef" />
      </main>
    </div>
  </div>
</template>
