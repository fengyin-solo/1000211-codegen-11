<template>
  <section class="page" data-module="shooting-progress">
    <header class="page-head">
      <div>
        <h2>拍摄日进度</h2>
        <p class="page-desc">按拍摄日期排列计划场次、完成场次、有效工时与超时情况，并汇总当天收工比例。</p>
      </div>
      <div class="page-actions">
        <button class="btn" type="button" @click="reload">刷新进度</button>
      </div>
    </header>

    <div class="stat-row">
      <article class="stat-card">
        <span class="stat-label">统计日期</span>
        <strong class="stat-value">{{ summary.date || '—' }}</strong>
      </article>
      <article class="stat-card">
        <span class="stat-label">当天拍摄日</span>
        <strong class="stat-value">{{ summary.total }}</strong>
      </article>
      <article class="stat-card">
        <span class="stat-label">当天已收工</span>
        <strong class="stat-value">{{ summary.wrapped }}</strong>
      </article>
      <article class="stat-card">
        <span class="stat-label">当天收工比例</span>
        <strong class="stat-value">{{ summary.wrapRatioText }}</strong>
      </article>
    </div>

    <form class="filter-bar" @submit.prevent="reload">
      <label class="filter-item">
        <span>统计日期</span>
        <input v-model="queryDate" type="date" />
      </label>
      <button class="btn" type="submit">查询</button>
      <button class="btn ghost" type="button" @click="resetDate">回到今天</button>
    </form>

    <table class="data-table">
      <thead>
        <tr>
          <th v-for="column in columns" :key="column">{{ column }}</th>
          <th>可执行动作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in days" :key="String(row.id)">
          <td v-for="column in columns" :key="column">{{ row[column] ?? '—' }}</td>
          <td class="row-actions">
            <button
              v-for="action in actions"
              :key="action"
              class="link"
              type="button"
              @click="runAction(action, row)"
            >
              {{ action }}
            </button>
          </td>
        </tr>
        <tr v-if="!days.length">
          <td :colspan="columns.length + 1" class="empty-state">暂无拍摄日排期，可先到拍摄进度登记拍摄日</td>
        </tr>
      </tbody>
    </table>

    <footer class="page-foot">
      <span>共 {{ days.length }} 个拍摄日</span>
      <span v-if="errorMessage" class="error-text">
        {{ errorMessage }}
        <button class="link" type="button" @click="reload">重试</button>
      </span>
    </footer>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { request } from '@/api/client'

type Row = Record<string, string | number | null>

const ENDPOINT = '/api/shooting/progress'
const ACTION_ENDPOINT = '/api/shooting'
const columns = ["拍摄日期", "拍摄日编号", "计划场次", "完成场次", "有效工时", "超时情况", "拍摄状态"]
const actions = ["开始拍摄", "确认收工", "申请顺延"]

const days = ref<Row[]>([])
const summary = ref({ date: '', total: 0, wrapped: 0, wrapRatioText: '—' })
const queryDate = ref('')
const errorMessage = ref('')

function resetDate() {
  queryDate.value = ''
  void reload()
}

async function runAction(action: string, row: Row) {
  errorMessage.value = ''
  try {
    const response = await request(`${ACTION_ENDPOINT}/${row.id}/actions`, {
      method: 'POST',
      body: JSON.stringify({ action }),
    })
    if (!response.ok) {
      throw new Error('拍摄进度动作未生效，请稍后重试')
    }
    await reload()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '拍摄进度操作失败'
  }
}

async function reload() {
  errorMessage.value = ''
  const query = queryDate.value ? `?date=${encodeURIComponent(queryDate.value)}` : ''
  try {
    const response = await request(`${ENDPOINT}${query}`)
    if (!response.ok) {
      throw new Error('拍摄日进度读取失败')
    }
    const payload = await response.json()
    days.value = payload.days ?? []
    const result = payload.summary ?? {}
    summary.value = {
      date: result.date ?? '',
      total: result.total ?? 0,
      wrapped: result.wrapped ?? 0,
      wrapRatioText: result.wrap_ratio_text ?? '—',
    }
  } catch (error) {
    // 读取失败时保留上次画面，只提示错误并允许重试
    errorMessage.value = error instanceof Error ? error.message : '拍摄日进度读取失败'
  }
}

onMounted(reload)
</script>
