"""拍摄日进度聚合：按拍摄日期汇总计划/完成场次、有效工时与超时情况。

这里是只读视图：只从 shooting 表里读数据并重新组织，不改写任何已有拍摄日记录，
也不影响分场大纲等其他模块的统计口径。
"""
from __future__ import annotations

import re
from datetime import date
from typing import Any

from app.store import store

MODULE = "shooting"
WRAPPED_STATUS = "已收工"

_NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?")


def _to_number(value: Any) -> float:
    """从字段值里取第一个数字；取不到就按 0 处理。

    示例数据里计划场次/有效工时既有数字也有「超时 1.5 小时」之类的文本，
    统一抽数字能让历史数据和后续登记的数据用同一口径汇总。
    """
    if isinstance(value, bool):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    matched = _NUMBER_RE.search(str(value or ""))
    return float(matched.group()) if matched else 0.0


def _is_overtime(value: Any) -> bool:
    """判断超时情况字段是否表示超时：出现「超时」且不是明确的否定说法。"""
    text = str(value or "").strip()
    if not text:
        return False
    if "无超时" in text or "未超时" in text or "不超时" in text:
        return False
    return "超时" in text


def _ratio_percent(part: int, total: int) -> int:
    if total <= 0:
        return 0
    return round(part * 100 / total)


def _date_key(row: dict[str, Any]) -> str:
    return str(row.get("拍摄日期") or "").strip()


def _build_day(day: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    planned = sum(int(_to_number(row.get("计划场次"))) for row in rows)
    completed = sum(int(_to_number(row.get("完成场次"))) for row in rows)
    work_hours = round(sum(_to_number(row.get("有效工时")) for row in rows), 1)
    overtime_rows = [row for row in rows if _is_overtime(row.get("超时情况"))]
    overtime_hours = round(
        sum(max(_to_number(row.get("超时情况")), 0.0) for row in overtime_rows), 1
    )
    wrapped = sum(1 for row in rows if row.get("status") == WRAPPED_STATUS)
    shooting_days = len(rows)
    return {
        "拍摄日期": day,
        "拍摄日数": shooting_days,
        "计划场次": planned,
        "完成场次": completed,
        "有效工时": work_hours,
        "超时场次": len(overtime_rows),
        "超时工时": overtime_hours,
        "已收工日数": wrapped,
        "收工比例": _ratio_percent(wrapped, shooting_days),
        "拍摄日编号": [str(row.get("拍摄日编号") or "") for row in rows],
        "拍摄地点": [str(row.get("拍摄地点") or "") for row in rows],
    }


def _sorted_group_keys(groups: dict[str, list[dict[str, Any]]]) -> list[str]:
    def sort_key(day: str) -> tuple[int, Any]:
        try:
            return (0, date.fromisoformat(day))
        except ValueError:
            # 日期缺失或格式异常时不参与正常日期排序，统一沉到末尾保留展示。
            return (1, day)

    return sorted(groups.keys(), key=sort_key)


def daily_progress() -> dict[str, Any]:
    """按拍摄日期升序返回拍摄日进度；同一天可能有多个拍摄日（多机位/多地点）。"""
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in store.rows(MODULE):
        groups.setdefault(_date_key(row), []).append(row)

    days = [_build_day(day, groups[day]) for day in _sorted_group_keys(groups)]
    totals = {
        "拍摄日数": sum(int(item["拍摄日数"]) for item in days),
        "计划场次": sum(int(item["计划场次"]) for item in days),
        "完成场次": sum(int(item["完成场次"]) for item in days),
        "有效工时": round(sum(float(item["有效工时"]) for item in days), 1),
        "超时场次": sum(int(item["超时场次"]) for item in days),
        "已收工日数": sum(int(item["已收工日数"]) for item in days),
        "已顺延日数": sum(
            1
            for row in store.rows(MODULE)
            if row.get("status") == "已顺延"
        ),
    }
    totals["收工比例"] = _ratio_percent(totals["已收工日数"], totals["拍摄日数"])
    return {"days": days, "totals": totals}


def current_day_snapshot(on_date: date | None = None) -> dict[str, Any]:
    """概览看板用的当天拍摄日快照。

    优先取系统当天所在拍摄日；当天没有排期时回退到最近的一个拍摄日，
    并在返回里标明实际指向的日期，方便看板如实说明。
    """
    today = on_date or date.today()
    today_key = today.isoformat()
    progress = daily_progress()
    days = progress["days"]

    if not days:
        return {
            "hasSchedule": False,
            "date": None,
            "isToday": False,
            "拍摄日数": 0,
            "已收工日数": 0,
            "收工比例": 0,
            "计划场次": 0,
            "完成场次": 0,
            "超时场次": 0,
        }

    by_date = {str(item["拍摄日期"]): item for item in days}
    target = by_date.get(today_key)
    if target is None:
        # days 已按日期升序，挑出不晚于今天的最后一天；今天之后才排期就取第一天。
        past = [item for item in days if _is_valid_date(str(item["拍摄日期"]))
                and date.fromisoformat(str(item["拍摄日期"])) <= today]
        target = past[-1] if past else days[0]

    return {
        "hasSchedule": True,
        "date": target["拍摄日期"],
        "isToday": target["拍摄日期"] == today_key,
        "拍摄日数": target["拍摄日数"],
        "已收工日数": target["已收工日数"],
        "收工比例": target["收工比例"],
        "计划场次": target["计划场次"],
        "完成场次": target["完成场次"],
        "超时场次": target["超时场次"],
    }


def _is_valid_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True
