<script setup lang="ts">
import { ref, onMounted } from 'vue'
import AppSidebar from './components/layout/AppSidebar.vue'
import ChatPanel from './components/chat/ChatPanel.vue'
import { useSessionStore } from './stores/session'

const sessionStore = useSessionStore()
const chatPanelRef = ref<InstanceType<typeof ChatPanel> | null>(null)

onMounted(async () => {
  await sessionStore.loadSessions()
  if (sessionStore.sessions.length === 0) {
    await handleCreateSession()
  }
})

function handleSelectSession(id: string) {
  chatPanelRef.value?.selectSession(id)
}

async function handleCreateSession() {
  await sessionStore.createSession()
  chatPanelRef.value?.createSession()
}
</script>

<template>
  <div class="flex h-screen bg-slate-900 text-white">
    <!-- 左侧边栏 -->
    <AppSidebar
      @select-session="handleSelectSession"
      @create-session="handleCreateSession"
    />

    <!-- 右侧主区域 -->
    <main class="flex-1 flex flex-col overflow-hidden">
      <ChatPanel ref="chatPanelRef" />
    </main>
  </div>
</template>
