"""
تحميل قاموس أسماء الأعمدة LFS ↔ نص السؤال (من MetaData_LFS_Training_Dataset)
واختيار مجموعة فرعية من الأعمدة لتقليل حجم الطلب إلى نموذج اللغة.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

_DATA_DIR = Path(__file__).resolve().parent / "data"
_LABELS_PATH = _DATA_DIR / "lfs_column_labels.json"

# أعمدة ذات أولوية لمسح القوى العاملة (تعليم، تشغيل، قطاع، نشاط، أسرة)
LFS_PRIORITY_COLUMNS: list[str] = [
    "f_m_id",
    "sample_id",
    "age",
    "gender",
    "gender_desc",
    "nationality",
    "nationality_desc",
    "family_relation",
    "family_relation_desc",
    "marage_status",
    "marage_status_desc",
    "q_301",
    "q_301_desc",
    "q_302",
    "q_302_e_txt",
    "q_303",
    "q_401",
    "q_501",
    "q_502",
    "q_503",
    "q_531",
    "q_531_desc",
    "q_532",
    "q_532_desc",
    "q_533",
    "q_533_desc",
    "q_534",
    "q_534_desc",
    "q_534_txt",
    "q_535",
    "q_535_txt",
    "q_536",
    "q_536_desc",
    "q_581_txt",
    "q_582_txt",
    "last_result",
    "last_result_desc_en",
    "visit_status_desc",
    "الملاحظة",
    "admin_name",
]


def _is_nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, float) and value != value:  # NaN
        return False
    s = str(value).strip()
    if not s or s.lower() == "nan":
        return False
    return True


@lru_cache(maxsize=1)
def load_default_labels() -> dict[str, str]:
    """تحميل القاموس من JSON المرفق مع الحزمة."""
    if not _LABELS_PATH.is_file():
        return {}
    try:
        raw = _LABELS_PATH.read_text(encoding="utf-8")
        data = json.loads(raw)
        return {str(k): str(v) for k, v in data.items() if isinstance(k, str)}
    except (OSError, json.JSONDecodeError):
        return {}


def merge_labels_for_columns(
    columns: list[str],
    default_labels: dict[str, str],
    override: Optional[dict[str, str]] = None,
) -> dict[str, str]:
    """دمج تسميات الأعمدة: افتراضي من الملف + أي تمرير يدوي من العميل."""
    out: dict[str, str] = {}
    override = override or {}
    for c in columns:
        if c in override and override[c]:
            out[c] = override[c]
        elif c in default_labels:
            out[c] = default_labels[c]
    return out


def select_columns_for_chunk(
    columns: list[str],
    records: list[dict[str, Any]],
    priority: list[str],
    max_cols: int,
) -> list[str]:
    """
    عند تجاوز max_cols: نأخذ أولاً الأعمدة ذات الأولوية الموجودة في الجدول،
    ثم الأعمدة التي لها قيمة غير فارغة في أي صف ضمن الدفعة،
    ثم بقية الأعمدة بالترتيب حتى الامتلاء.
    """
    if max_cols <= 0 or len(columns) <= max_cols:
        return list(columns)

    used: set[str] = set()
    for rec in records:
        for c in columns:
            if c == "row_index":
                continue
            if _is_nonempty(rec.get(c)):
                used.add(c)

    out: list[str] = []
    seen: set[str] = set()

    for p in priority:
        if p in columns and p not in seen:
            out.append(p)
            seen.add(p)
        if len(out) >= max_cols:
            return out

    for c in columns:
        if c == "row_index":
            continue
        if c in used and c not in seen:
            out.append(c)
            seen.add(c)
        if len(out) >= max_cols:
            return out

    for c in columns:
        if c == "row_index" or c in seen:
            continue
        out.append(c)
        seen.add(c)
        if len(out) >= max_cols:
            break

    return out[:max_cols]


def max_columns_from_env() -> int:
    return max(24, int(os.getenv("LFS_MAX_COLUMNS", "96")))


def slice_record_to_columns(rec: dict[str, Any], cols: list[str]) -> dict[str, Any]:
    row_index = rec.get("row_index")
    out: dict[str, Any] = {"row_index": row_index}
    for c in cols:
        if c in rec:
            out[c] = rec.get(c)
    return out
