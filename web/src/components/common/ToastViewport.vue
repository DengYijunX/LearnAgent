<script setup lang="ts">
import { CircleCheck, CircleX, X } from 'lucide-vue-next'

export interface ToastMessage {
  id: number
  tone: 'success' | 'error'
  text: string
}

defineProps<{ messages: ToastMessage[] }>()
const emit = defineEmits<{ (e: 'dismiss', id: number): void }>()
</script>

<template>
  <div class="fixed right-6 top-6 z-[70] w-[320px] space-y-2" aria-live="polite" aria-atomic="false">
    <div
      v-for="message in messages"
      :key="message.id"
      class="glass-panel flex items-start gap-3 rounded-[15px] bg-white/92 px-4 py-3 text-[12px] shadow-xl"
    >
      <CircleCheck v-if="message.tone === 'success'" :size="17" class="mt-0.5 shrink-0 text-emerald-600" />
      <CircleX v-else :size="17" class="mt-0.5 shrink-0 text-red-600" />
      <p class="flex-1 leading-5 text-[var(--ink-secondary)]">{{ message.text }}</p>
      <button type="button" class="focus-ring cursor-pointer rounded-md p-1 text-[var(--ink-muted)] hover:bg-slate-100" aria-label="关闭提示" @click="emit('dismiss', message.id)">
        <X :size="13" />
      </button>
    </div>
  </div>
</template>
