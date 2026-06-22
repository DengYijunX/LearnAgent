<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  status: string
  label: string
}>()

const colorClasses = computed(() => {
  switch (props.status) {
    case 'success':
    case 'default':
      return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
    case 'warning':
    case 'plan':
      return 'bg-amber-500/20 text-amber-400 border-amber-500/30'
    case 'error':
      return 'bg-red-500/20 text-red-400 border-red-500/30'
    default:
      return 'bg-slate-500/20 text-slate-400 border-slate-500/30'
  }
})
</script>

<template>
  <span
    class="px-2 py-0.5 text-xs rounded-full border"
    :class="colorClasses"
  >
    {{ label }}
  </span>
</template>
