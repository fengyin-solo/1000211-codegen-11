<template>
  <section class="page">
    <header class="page-head">
      <div>
        <h2>运营概览</h2>
        <p class="page-desc">汇总各业务模块的关键指标，先看总量再看异常。</p>
      </div>
    </header>

    <div v-if="overviewError" class="retry-bar">
      <span class="error-text">{{ overviewError }}</span>
      <button class="btn" type="button" :disabled="loading" @click="reload">重试</button>
    </div>

    <div class="stat-row">
      <article v-for="card in cards" :key="card.label" class="stat-card">
        <span class="stat-label">{{ card.label }}</span>
        <strong class="stat-value">{{ card.value }}</strong>
      </article>
      <article class="stat-card shooting-card">
        <span class="stat-label">
          当天收工比例
          <small v-if="shootingDay.hasSchedule">（{{ shootingDay.date }}{{ shootingDay.isToday ? '' : ' 最近排期' }}）</small>
        </span>
        <template v-if="shootingDay.hasSchedule">
          <strong class="stat-value">{{ shootingDay['收工比例'] }}%</strong>
          <div class="ratio-bar"><span :style="{ width: `${shootingDay['收工比例']}%` }"></span></div>
          <small class="ratio-hint">
            已收工 {{ shootingDay['已收工日数'] }}/{{ shootingDay['拍摄日数'] }} 个拍摄日 ·
            场次 {{ shootingDay['完成场次'] }}/{{ shootingDay['计划场次'] }}
            <template v-if="shootingDay['超时场次'] > 0"> · 超时 {{ shootingDay['超时场次'] }}</template>
          </small>
        </template>
        <template v-else>
          <strong class="stat-value">—</strong>
          <small class="ratio-hint">暂无排期</small>
        </template>
      </article>
    </div>

    <table v-if="moduleRows.length" class="data-table">
      <thead>
        <tr><th>业务模块</th><th>今日新增</th><th>待处理</th><th>异常量</th></tr>
      </thead>
      <tbody>
        <tr v-for="row in moduleRows" :key="row.name">
          <td>{{ row.name }}</td>
          <td>{{ row.created }}</td>
          <td>{{ row.pending }}</td>
          <td>{{ row.abnormal }}</td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { request } from '@/api/client'

type ShootingDaySnapshot = {
  hasSchedule: boolean
  date: string | null
  isToday: boolean
  拍摄日数: number
  已收工日数: number
  收工比例: number
  计划场次: number
  完成场次: number
  超时场次: number
}

type Overview = {
  cards: { label: string; value: number }[]
  modules: { name: string; created: number; pending: number; abnormal: number }[]
  shootingDay: ShootingDaySnapshot
}

function emptySnapshot(): ShootingDaySnapshot {
  return {
    hasSchedule: false,
    date: null,
    isToday: false,
    拍摄日数: 0,
    已收工日数: 0,
    收工比例: 0,
    计划场次: 0,
    完成场次: 0,
    超时场次: 0,
  }
}

const cards = ref<Overview['cards']>([])
const moduleRows = ref<Overview['modules']>([])
const shootingDay = ref<ShootingDaySnapshot>(emptySnapshot())
const overviewError = ref('')
const loading = ref(false)
// 区分「从未成功读取」与「读取失败」：失败时保留上次画面与数值。
const loadedOnce = ref(false)

async function reload() {
  loading.value = true
  overviewError.value = ''
  try {
    const response = await request('/api/overview')
    if (!response.ok) {
      throw new Error(`概览数据读取失败（${response.status}）`)
    }
    const payload = (await response.json()) as Overview
    cards.value = payload.cards ?? []
    moduleRows.value = payload.modules ?? []
    shootingDay.value = payload.shootingDay ?? emptySnapshot()
    loadedOnce.value = true
  } catch (error) {
    overviewError.value = error instanceof Error ? error.message : '概览数据读取失败'
  } finally {
    loading.value = false
  }
}

onMounted(reload)
</script>

<style scoped>
.retry-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #fef3f2;
  border: 1px solid #fda29b;
  border-radius: 8px;
  padding: 8px 12px;
  margin-bottom: 12px;
}
.shooting-card {
  max-width: 280px;
}
.shooting-card small {
  font-weight: 400;
  color: var(--muted);
}
.ratio-bar {
  height: 8px;
  background: #e5e7eb;
  border-radius: 999px;
  overflow: hidden;
  margin: 6px 0 4px;
}
.ratio-bar span {
  display: block;
  height: 100%;
  background: var(--brand);
}
.ratio-hint {
  font-size: 12px;
  color: var(--muted);
}
</style>
