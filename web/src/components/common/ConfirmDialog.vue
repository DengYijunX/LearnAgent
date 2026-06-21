<script setup lang="ts">
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { AlertTriangle } from 'lucide-vue-next'

const props = withDefaults(defineProps<{
  open: boolean
  title: string
  description: string
  confirmLabel?: string
  danger?: boolean
}>(), { confirmLabel: '确认', danger: false })

const emit = defineEmits<{
  (e: 'confirm'): void
  (e: 'cancel'): void
}>()

const dialogRef = ref<HTMLElement | null>(null)
const cancelRef = ref<HTMLButtonElement | null>(null)
let previousFocus: HTMLElement | null = null

function cancel() { emit('cancel') }

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    event.preventDefault()
    cancel()
    return
  }
  if (event.key !== 'Tab' || !dialogRef.value) return
  const focusables = Array.from(dialogRef.value.querySelectorAll<HTMLElement>('button:not([disabled])'))
  if (!focusables.length) return
  const first = focusables[0]
  const last = focusables[focusables.length - 1]
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault(); last.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault(); first.focus()
  }
}

watch(() => props.open, async open => {
  if (open) {
    previousFocus = document.activeElement as HTMLElement
    await nextTick()
    cancelRef.value?.focus()
  } else {
    previousFocus?.focus()
    previousFocus = null
  }
})

onBeforeUnmount(() => previousFocus?.focus())
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="fixed inset-0 z-[80] flex items-center justify-center p-6" @keydown="handleKeydown">
      <div class="absolute inset-0 bg-[#24334b]/26 backdrop-blur-[7px]" aria-hidden="true" @click="cancel" />
      <section ref="dialogRef" role="dialog" aria-modal="true" aria-labelledby="confirm-title" class="glass-panel relative w-full max-w-[420px] rounded-[22px] bg-white/94 p-5 shadow-2xl">
        <div class="flex gap-3.5">
          <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-[13px] bg-amber-50 text-amber-700"><AlertTriangle :size="19" /></span>
          <div>
            <h2 id="confirm-title" class="text-[16px] font-semibold text-[var(--ink)]">{{ title }}</h2>
            <p class="mt-1.5 text-[12px] leading-5 text-[var(--ink-secondary)]">{{ description }}</p>
          </div>
        </div>
        <div class="mt-5 flex justify-end gap-2">
          <button ref="cancelRef" type="button" class="focus-ring cursor-pointer rounded-[11px] px-4 py-2 text-[12px] font-semibold text-[var(--ink-secondary)] hover:bg-slate-100" @click="cancel">取消</button>
          <button type="button" class="focus-ring cursor-pointer rounded-[11px] px-4 py-2 text-[12px] font-semibold text-white" :class="danger ? 'bg-red-600 hover:bg-red-700' : 'bg-[var(--primary)] hover:bg-[var(--primary-strong)]'" @click="emit('confirm')">{{ confirmLabel }}</button>
        </div>
      </section>
    </div>
  </Teleport>
</template>
