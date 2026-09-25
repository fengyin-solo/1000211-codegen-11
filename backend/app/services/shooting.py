"""拍摄进度业务规则：状态流转、字段校验与筛选口径都收在这里。"""
from __future__ import annotations

from datetime import date
from typing import Any

from app.store import store

MODULE = "shooting"
REQUIRED_FIELDS = ["拍摄日编号", "拍摄日期", "拍摄地点"]
STATUS_ORDER = ["待拍摄", "拍摄中", "已收工", "已顺延"]
ACTION_RULES = {"开始拍摄": "拍摄中", "确认收工": "已收工", "申请顺延": "已顺延"}
NEGATIVE_ACTIONS = []


class ShootingService:
    def list_entries(
        self,
        *,
        keyword: str | None = None,
        status: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        rows = store.rows(MODULE)
        if keyword:
            rows = [row for row in rows if keyword in str(row.get("拍摄日编号", ""))]
        if status:
            rows = [row for row in rows if row.get("status") == status]
        total = len(rows)
        start = max(page - 1, 0) * size
        return rows[start:start + size], total

    def get_entry(self, entry_id: int) -> dict[str, Any] | None:
        return store.find(MODULE, entry_id)

    def create_entry(self, values: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
        missing = [field for field in REQUIRED_FIELDS if not str(values.get(field) or "").strip()]
        if missing:
            return None, missing
        rows = store.rows(MODULE)
        entry = {"id": max((int(row.get("id", 0)) for row in rows), default=0) + 1}
        entry.update({field: values.get(field) for field in REQUIRED_FIELDS})
        entry["status"] = STATUS_ORDER[0]
        entry["pending"] = True
        entry["abnormal"] = False
        rows.append(entry)
        return entry, []

    def run_action(self, entry_id: int, action: str) -> tuple[dict[str, Any] | None, str]:
        entry = store.find(MODULE, entry_id)
        if entry is None:
            return None, f"拍摄日 {entry_id} 不存在或已归档"
        if action not in ACTION_RULES:
            return None, f"动作「{action}」不属于拍摄进度可执行范围"
        target = ACTION_RULES[action]
        if target not in STATUS_ORDER:
            return None, f"目标状态「{target}」不在允许的状态序列里"
        entry["status"] = target
        entry["pending"] = target != STATUS_ORDER[-1]
        entry["abnormal"] = action in NEGATIVE_ACTIONS
        return entry, f"拍摄日已{action}"

    def day_progress(self, *, on_date: str | None = None) -> dict[str, Any]:
        """拍摄日进度视图：按拍摄日期升序排出计划/完成场次、有效工时与超时情况，
        并汇总当天收工比例。只读取已有记录，不改写任何场次统计。"""
        rows = sorted(store.rows(MODULE), key=lambda row: str(row.get("拍摄日期") or ""))
        days = [
            {
                "id": row.get("id"),
                "拍摄日编号": row.get("拍摄日编号"),
                "拍摄日期": row.get("拍摄日期"),
                "计划场次": row.get("计划场次"),
                "完成场次": row.get("完成场次"),
                "有效工时": row.get("有效工时"),
                "超时情况": row.get("超时情况"),
                "拍摄状态": row.get("status"),
                "status": row.get("status"),
            }
            for row in rows
        ]
        target = (on_date or "").strip() or date.today().isoformat()
        todays = [row for row in rows if str(row.get("拍摄日期") or "") == target]
        wrapped = sum(1 for row in todays if row.get("status") == "已收工")
        total = len(todays)
        ratio = wrapped / total if total else 0.0
        summary = {
            "date": target,
            "total": total,
            "wrapped": wrapped,
            "wrap_ratio": ratio,
            "wrap_ratio_text": f"{ratio:.0%}",
        }
        return {"days": days, "summary": summary}

    def wrap_ratio_card(self) -> dict[str, Any]:
        """概览看板用的「当天收工比例」卡片，与进度视图共用同一份汇总结果。"""
        summary = self.day_progress()["summary"]
        return {"label": "当天收工比例", "value": summary["wrap_ratio_text"]}
