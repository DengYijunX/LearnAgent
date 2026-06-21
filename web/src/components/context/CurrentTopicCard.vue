<script setup lang="ts">
import { nextTick, ref } from 'vue'
import { BookOpen, Check, Compass, Pencil, Sparkles, X } from 'lucide-vue-next'

const props = defineProps<{
  topic: string | null
  intent: string
  mode: 'default' | 'plan'
}>()

const emit = defineEmits<{
  (e: 'set-topic', topic: string): void
  (e: 'toggle-mode'): void
}>()

const editing = ref(false)
const draft = ref('')
const inputRef = ref<HTMLInputElement | null>(null)

async function beginEdit() {
  draft.value = props.topic || ''
  editing.value = true
  await nextTick()
  inputRef.value?.focus()
}

function save() {
  const topic = draft.value.trim()
  if (!topic) return
  emit('set-topic', topic)
  editing.value = false
}
</script>

<template>
  <section class="context-card" aria-labelledby="topic-card-title">
    <div class="context-card-title-row">
      <div class="flex items-center gap-2">
        <span class="context-card-icon bg-blue-50 text-blue-700"><BookOpen :size="15" /></span>
        <h3 id="topic-card-title" class="context-card-title">当前学习</h3>
      </div>
      <button v-if="!editing" type="button" class="context-icon-button" aria-label="编辑当前主题" @click="beginEdit">
        <Pencil :size="13" />
      </button>
    </div>

    <div v-if="editing" class="mt-3 flex items-center gap-1.5">
      <input
        ref="inputRef"
        v-model="draft"
        class="focus-ring min-w-0 flex-1 rounded-[10px] border border-blue-100 bg-white/80 px-2.5 py-2 text-[12px] text-[var(--ink)] outline-none"
        maxlength="80"
        placeholder="输入当前学习主题"
        @keydown.enter="save"
        @keydown.esc="editing = false"
      >
      <button type="button" class="context-icon-button text-blue-700" aria-label="保存主题" @click="save"><Check :size="14" /></button>
      <button type="button" class="context-icon-button" aria-label="取消编辑" @click="editing = false"><X :size="14" /></button>
    </div>
    <div v-else class="mt-3">
      <p class="text-[14px] font-semibold leading-5 text-[var(--ink)]">{{ topic || '尚未设定主题' }}</p>
      <p class="mt-1 text-[11px] text-[var(--ink-muted)]">意图 · {{ intent || 'chat' }}</p>
    </div>

    <button type="button" class="focus-ring mt-3 flex w-full cursor-pointer items-center justify-between rounded-[11px] border border-white/75 bg-white/55 px-3 py-2.5 text-[11px] font-semibold text-[var(--ink-secondary)] transition hover:bg-white/90" @click="emit('toggle-mode')">
      <span class="flex items-center gap-2">
        <Compass v-if="mode === 'plan'" :size="14" class="text-amber-600" />
        <Sparkles v-else :size="14" class="text-blue-600" />
        {{ mode === 'plan' ? '探索模式' : '完整模式' }}
      </span>
      <span class="font-normal text-[var(--ink-muted)]">点击切换</span>
    </button>
  </section>
</template>
