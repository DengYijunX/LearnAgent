<script setup lang="ts">
import { ref } from 'vue'
import { BookMarked, ChevronDown } from 'lucide-vue-next'
import type { LearningMemory } from '../../types/api'

defineProps<{ memories: LearningMemory[]; error?: string }>()
const expanded = ref(new Set<string>())
function toggle(name: string) {
  const next = new Set(expanded.value)
  next.has(name) ? next.delete(name) : next.add(name)
  expanded.value = next
}
</script>

<template>
  <section class="context-card" aria-labelledby="memory-card-title">
    <div class="context-card-title-row">
      <div class="flex items-center gap-2">
        <span class="context-card-icon bg-amber-50 text-amber-700"><BookMarked :size="15" /></span>
        <h3 id="memory-card-title" class="context-card-title">学习记忆</h3>
      </div>
      <span v-if="memories.length" class="text-[10px] text-[var(--ink-muted)]">最近 {{ memories.length }} 条</span>
    </div>
    <p v-if="error" class="context-error">{{ error }}</p>
    <p v-else-if="!memories.length" class="context-empty">暂无可展示的学习记忆</p>
    <div v-else class="mt-2.5 divide-y divide-white/75">
      <button v-for="memory in memories" :key="memory.name" type="button" class="focus-ring block w-full cursor-pointer py-2.5 text-left" @click="toggle(memory.name)">
        <span class="flex items-center gap-2">
          <span class="min-w-0 flex-1 truncate text-[11px] font-semibold text-[var(--ink-secondary)]">{{ memory.name }}</span>
          <ChevronDown :size="12" class="shrink-0 text-[var(--ink-muted)] transition-transform" :class="expanded.has(memory.name) ? 'rotate-180' : ''" />
        </span>
        <span class="mt-1 block text-[10px] leading-4 text-[var(--ink-muted)]" :class="expanded.has(memory.name) ? '' : 'line-clamp-2'">{{ expanded.has(memory.name) ? (memory.body || memory.description) : memory.description }}</span>
      </button>
    </div>
  </section>
</template>
