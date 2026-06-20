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
  <div class="flex h-screen bg-[#f5f7fb] text-slate-700">
    <AppSidebar
      @select-session="handleSelectSession"
      @create-session="handleCreateSession"
    />
    <main class="flex-1 flex flex-col overflow-hidden">
      <ChatPanel ref="chatPanelRef" />
    </main>
  </div>
</template>
