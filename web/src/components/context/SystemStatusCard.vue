<script setup lang="ts">
import { KeyRound, Server, ShieldCheck, Wifi, WifiOff } from 'lucide-vue-next'
import type { ConfigInfo } from '../../types/api'

defineProps<{ config: ConfigInfo | null; connected: boolean; error?: string }>()
</script>

<template>
  <section class="context-card" aria-labelledby="system-card-title">
    <div class="context-card-title-row">
      <div class="flex items-center gap-2">
        <span class="context-card-icon bg-emerald-50 text-emerald-700"><ShieldCheck :size="15" /></span>
        <h3 id="system-card-title" class="context-card-title">系统状态</h3>
      </div>
    </div>
    <p v-if="error" class="context-error">{{ error }}</p>
    <div v-else class="mt-3 grid gap-2 text-[10px]">
      <div class="flex items-center gap-2 text-[var(--ink-secondary)]">
        <Wifi v-if="connected" :size="13" class="text-emerald-600" /><WifiOff v-else :size="13" class="text-slate-400" />
        <span class="flex-1">会话连接</span><strong :class="connected ? 'text-emerald-700' : 'text-[var(--ink-muted)]'">{{ connected ? '正常' : '未连接' }}</strong>
      </div>
      <div class="flex items-center gap-2 text-[var(--ink-secondary)]">
        <Server :size="13" class="text-slate-500" /><span class="flex-1">模型模式</span><strong>{{ config?.model_mode || '—' }}</strong>
      </div>
      <div class="flex items-center gap-2 text-[var(--ink-secondary)]">
        <KeyRound :size="13" class="text-slate-500" /><span class="flex-1">API 凭据</span><strong :class="config?.api_key_configured ? 'text-emerald-700' : 'text-amber-700'">{{ config?.api_key_configured ? '已配置' : '未配置' }}</strong>
      </div>
    </div>
  </section>
</template>
