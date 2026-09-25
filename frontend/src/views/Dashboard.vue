<template>
  <section class="page">
    <header class="page-head">
      <div>
        <h2>运营概览</h2>
        <p class="page-desc">汇总各业务模块的关键指标，先看总量再看异常。</p>
      </div>
    </header>
    <div class="stat-row">
      <article v-for="card in cards" :key="card.label" class="stat-card">
        <span class="stat-label">{{ card.label }}</span>
        <strong class="stat-value">{{ card.value }}</strong>
      </article>
    </div>
    <table class="data-table">
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
    <footer v-if="errorMessage" class="page-foot">
      <span class="error-text">{{ errorMessage }}</span>
      <button class="btn" type="button" @click="loadOverview">重试</button>
    </footer>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { fetchJson } from '@/api/client'

type Overview = {
  cards: { label: string; value: number | string }[]
  modules: { name: string; created: number; pending: number; abnormal: number }[]
}

const cards = ref<Overview['cards']>([{"label": "业务模块", "value": 0}, {"label": "今日新增", "value": 0}, {"label": "待处理", "value": 0}, {"label": "异常量", "value": 0}, {"label": "当天收工比例", "value": "—"}])
const moduleRows = ref<Overview['modules']>([{"name": "剧本管理", "created": 0, "pending": 0, "abnormal": 0}, {"name": "分场大纲", "created": 0, "pending": 0, "abnormal": 0}, {"name": "角色选角", "created": 0, "pending": 0, "abnormal": 0}, {"name": "剧组人员", "created": 0, "pending": 0, "abnormal": 0}, {"name": "拍摄通告", "created": 0, "pending": 0, "abnormal": 0}, {"name": "场地租用", "created": 0, "pending": 0, "abnormal": 0}, {"name": "道具管理", "created": 0, "pending": 0, "abnormal": 0}, {"name": "服装造型", "created": 0, "pending": 0, "abnormal": 0}, {"name": "化妆造型", "created": 0, "pending": 0, "abnormal": 0}, {"name": "器材管理", "created": 0, "pending": 0, "abnormal": 0}, {"name": "拍摄进度", "created": 0, "pending": 0, "abnormal": 0}, {"name": "素材管理", "created": 0, "pending": 0, "abnormal": 0}, {"name": "后期剪辑", "created": 0, "pending": 0, "abnormal": 0}, {"name": "特效制作", "created": 0, "pending": 0, "abnormal": 0}, {"name": "审片意见", "created": 0, "pending": 0, "abnormal": 0}, {"name": "预算科目", "created": 0, "pending": 0, "abnormal": 0}, {"name": "费用报销", "created": 0, "pending": 0, "abnormal": 0}, {"name": "档期协调", "created": 0, "pending": 0, "abnormal": 0}, {"name": "外景许可", "created": 0, "pending": 0, "abnormal": 0}, {"name": "杀青结算", "created": 0, "pending": 0, "abnormal": 0}])
const errorMessage = ref('')

async function loadOverview() {
  errorMessage.value = ''
  try {
    const payload = await fetchJson<Overview>('/api/overview')
    cards.value = payload.cards
    moduleRows.value = payload.modules
  } catch {
    // 读取失败时保留上次画面，只提示错误并允许重试
    errorMessage.value = '运营概览读取失败，请稍后重试'
  }
}

onMounted(loadOverview)
</script>
