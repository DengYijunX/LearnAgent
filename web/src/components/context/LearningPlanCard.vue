<script setup lang="ts">
import { computed, ref } from 'vue'
import { CheckCircle2, ChevronDown, Circle, ListChecks, LoaderCircle } from 'lucide-vue-next'
import type { LearningTodo } from '../../types/api'

const props = defineProps<{ todos: LearningTodo[]; error?: string }>()
const showCompleted = ref(false)
const active = computed(() => props.todos.filter(item => item.status !== 'completed'))
const completed = computed(() => props.todos.filter(item => item.status === 'completed'))
</script>

<template>
  <section class="context-card" aria-labelledby="plan-card-title">
    <div class="context-card-title-row">
      <div class="flex items-center gap-2">
        <span class="context-card-icon bg-violet-50 text-violet-700"><ListChecks :size="15" /></span>
        <h3 id="plan-card-title" class="context-card-title">学习计划</h3>
      </div>
      <span v-if="todos.length" class="text-[10px] font-semibold text-[var(--ink-muted)]">{{ completed.length }}/{{ todos.length }}</span>
    </div>

    <p v-if="error" class="context-error">{{ error }}</p>
    <p v-else-if="!todos.length" class="context-empty">Agent 生成学习计划后会显示在这里</p>
    <div v-else class="mt-3 space-y-2.5">
      <div v-for="item in active" :key="`${item.status}-${item.content}`" class="flex gap-2.5">
        <LoaderCircle v-if="item.status === 'in_progress'" :size="14" class="mt-0.5 shrink-0 animate-spin text-blue-600" />
        <Circle v-else :size="14" class="mt-0.5 shrink-0 text-slate-300" />
        <div class="min-w-0">
          <p class="text-[11px] leading-[17px] text-[var(--ink-secondary)]">{{ item.content }}</p>
          <p v-if="item.status === 'in_progress' && item.active_form" class="mt-0.5 text-[10px] text-blue-600">{{ item.active_form }}</p>
        </div>
      </div>

      <button v-if="completed.length" type="button" class="focus-ring flex cursor-pointer items-center gap-1.5 rounded-md text-[10px] font-semibold text-[var(--ink-muted)] hover:text-[var(--ink-secondary)]" @click="showCompleted = !showCompleted">
        <ChevronDown :size="12" :class="showCompleted ? 'rotate-180' : ''" class="transition-transform" />
        已完成 {{ completed.length }} 项
      </button>
      <div v-if="showCompleted" class="space-y-2 border-t border-white/70 pt-2.5">
        <div v-for="item in completed" :key="item.content" class="flex gap-2">
          <CheckCircle2 :size="13" class="mt-0.5 shrink-0 text-emerald-600" />
          <p class="text-[10px] leading-4 text-[var(--ink-muted)] line-through decoration-slate-300">{{ item.content }}</p>
        </div>
      </div>
    </div>
  </section>
</template>
