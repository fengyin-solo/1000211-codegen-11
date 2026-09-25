<template>
  <section class="page" data-module="shooting-progress">
    <header class="page-head">
      <div>
        <h2>拍摄日进度</h2>
        <p class="page-desc">按拍摄日期排列计划场次、完成场次、有效工时与超时情况；开工、收工或顺延后与拍摄进度列表保持一致。</p>
      </div>
      <div class="page-actions">
        <button class="btn" type="button" :disabled="loading" @click="reload">
          {{ loading ? '刷新中…' : '刷新进度' }}
        </button>
        <RouterLink class="btn ghost" to="/shooting">前往拍摄进度操作</RouterLink>
      </div>
    </header>

    <div v-if="hasData" class="stat-row">
      <article v-for="item in statCards" :key="item.label" class="stat-card">
        <span class="stat-label">{{ item.label }}</span>
        <strong class="stat-value">{{ item.value }}</strong>
      </article>
    </div>

    <div v-if="errorMessage" class="retry-bar">
      <span class="error-text">{{ errorMessage }}</span>
      <button class="btn" type="button" :disabled="loading" @click="reload">重试</button>
    </div>

    <table v-if="hasData" class="data-table">
      <thead>
        <tr>
          <th v-for="column in columns" :key="column">{{ column }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="day in days" :key="String(day['拍摄日期'])">
          <td>{{ day['拍摄日期'] || '未排日期' }}</td>
          <td>{{ day['拍摄日数'] }}</td>
          <td>{{ day['计划场次'] }}</td>
          <td>{{ day['完成场次'] }}</td>
          <td>{{ day['有效工时'] }} 小时</td>
          <td>
            <span v-if="day['超时场次'] > 0" class="overtime-badge">
              {{ day['超时场次'] }} 个拍摄日 · {{ day['超时工时'] }} 小时
            </span>
            <span v-else>正常</span>
          </td>
          <td>{{ day['已收工日数'] }}/{{ day['拍摄日数'] }}</td>
          <td>
            <div class="ratio-cell">
              <div class="ratio-bar"><span :style="{ width: `${day['收工比例']}%` }"></span></div>
              <em>{{ day['收工比例'] }}%</em>
            </div>
          </td>
        </tr>
      </tbody>
    </table>

    <footer v-if="hasData" class="page-foot">
      <span>共 {{ days.length }} 个拍摄日期 · {{ totals['拍摄日数'] }} 个拍摄日</span>
      <span v-if="!errorMessage">数据与拍摄进度列表来自同一接口口径</span>
    </footer>

    <div v-if="showEmpty" class="empty-panel">
      <strong>暂无排期</strong>
      <p>还没有任何拍摄日，先到拍摄进度里登记拍摄日，进度会自动按日期汇总。</p>
      <RouterLink class="btn primary" to="/shooting">去登记拍摄日</RouterLink>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { request } from '@/api/client'

const ENDPOINT = '/api/shooting/progress/daily'
const columns = ['拍摄日期', '拍摄日数', '计划场次', '完成场次', '有效工时', '超时情况', '收工', '当天收工比例']

type DayRow = {
  拍摄日期: string
  拍摄日数: number
  计划场次: number
  完成场次: number
  有效工时: number
  超时场次: number
  超时工时: number
  已收工日数: number
  收工比例: number
}

type Totals = {
  拍摄日数: number
  计划场次: number
  完成场次: number
  有效工时: number
  超时场次: number
  已收工日数: number
  已顺延日数: number
  收工比例: number
}

type DailyPayload = { days: DayRow[]; totals: Totals }

function emptyTotals(): Totals {
  return {
    拍摄日数: 0,
    计划场次: 0,
    完成场次: 0,
    有效工时: 0,
    超时场次: 0,
    已收工日数: 0,
    已顺延日数: 0,
    收工比例: 0,
  }
}

const days = ref<DayRow[]>([])
const totals = ref<Totals>(emptyTotals())
const loading = ref(false)
const errorMessage = ref('')
// 只在「请求已完成且确认没有拍摄日」时展示排期空态；
// 加载中或读取失败都不算空，失败时保留上次画面。
const loadedOnce = ref(false)

const hasData = computed(() => days.value.length > 0)
const showEmpty = computed(() => loadedOnce.value && !hasData.value && !errorMessage.value)

const statCards = computed(() => [
  { label: '拍摄日数', value: totals.value.拍摄日数 },
  { label: '计划场次', value: totals.value.计划场次 },
  { label: '完成场次', value: totals.value.完成场次 },
  { label: '累计有效工时', value: `${totals.value.有效工时} 小时` },
  { label: '超时拍摄日', value: totals.value.超时场次 },
  { label: '已顺延', value: totals.value.已顺延日数 },
  { label: '整体收工比例', value: `${totals.value.收工比例}%` },
])

async function reload() {
  loading.value = true
  errorMessage.value = ''
  try {
    const response = await request(ENDPOINT)
    if (!response.ok) {
      throw new Error(`拍摄日进度读取失败（${response.status}）`)
    }
    const payload = (await response.json()) as DailyPayload
    days.value = payload.days ?? []
    totals.value = payload.totals ?? emptyTotals()
    loadedOnce.value = true
  } catch (error) {
    // 不清空 days/totals：保留上次画面，仅提示并允许重试。
    errorMessage.value = error instanceof Error ? error.message : '拍摄日进度读取失败'
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
.overtime-badge {
  color: #b42318;
}
.ratio-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}
.ratio-bar {
  width: 90px;
  height: 8px;
  background: #e5e7eb;
  border-radius: 999px;
  overflow: hidden;
}
.ratio-bar span {
  display: block;
  height: 100%;
  background: var(--brand);
}
.ratio-cell em {
  font-style: normal;
  font-size: 12px;
  color: var(--muted);
}
.empty-panel {
  background: #fff;
  border: 1px dashed var(--border);
  border-radius: 8px;
  padding: 40px 16px;
  text-align: center;
  color: var(--muted);
}
.empty-panel strong {
  display: block;
  color: #1f2937;
  font-size: 16px;
  margin-bottom: 8px;
}
.empty-panel p {
  margin: 0 0 16px;
  font-size: 13px;
}
</style>
