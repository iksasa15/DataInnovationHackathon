#!/usr/bin/env python3
"""
تقييم تقريبي: مقارنة مخرجات التحقق مع عمود «الملاحظة» في LFS_Training_Dataset.
يعمل بدون مفتاح API (وضع fast = قواعد محلية + طبقة hybrid).

يتطلّب: pip install -r backend/requirements-scripts.txt

الاستخدام من جذر المستودع:
  backend/.venv/bin/python backend/scripts/eval_lfs_notes.py

أو من مجلد backend:
  python scripts/eval_lfs_notes.py

أو مع ملف مخصص:
  backend/.venv/bin/python backend/scripts/eval_lfs_notes.py path/to/LFS_Training_Dataset\\ 3.xlsx
"""

from __future__ import annotations

import asyncio
import os
import re
import sys
from pathlib import Path

# جذر backend على sys.path
_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

import pandas as pd

from validator import validate_rows_dynamic


def _keywords_from_note(note: str) -> set[str]:
    if not isinstance(note, str) or not note.strip():
        return set()
    keys: set[str] = set()
    # كلمات عربية (3 أحرف فأكثر) من نص الملاحظة نفسه
    for w in re.findall(r"[\u0600-\u06FF]{3,}", note):
        if w not in {"الحقل", "حقل", "إلى"}:
            keys.add(w)
    # رموز حقول شائعة في الملاحظات التوضيحية
    for code in ("q_534", "q_535", "q_536", "q_534_desc"):
        if code in note:
            keys.add(code.replace("_desc", ""))
    return keys


def _output_hits_keywords(text: str, keywords: set[str]) -> bool:
    if not keywords:
        return False
    t = (text or "").lower()
    for k in keywords:
        if k.lower() in t:
            return True
    return False


async def main() -> None:
    root = Path(__file__).resolve().parents[2]
    xlsx = Path(sys.argv[1]) if len(sys.argv) > 1 else root / "LFS_Training_Dataset 3.xlsx"
    if not xlsx.is_file():
        print(f"ملف غير موجود: {xlsx}")
        sys.exit(1)

    df = pd.read_excel(xlsx, sheet_name=0)
    columns = [str(c) for c in df.columns]
    records = []
    for i, row in df.iterrows():
        rec = {"row_index": int(i), **{c: row[c] for c in columns}}
        records.append(rec)

    os.environ.setdefault("LFS_MAX_COLUMNS", "96")

    out = await validate_rows_dynamic(
        columns,
        records,
        mode="fast",
        embed_metadata=True,
        column_subset=True,
        apply_hybrid_rules=True,
    )

    note_col = "الملاحظة"
    hits = 0
    total = 0
    for r in out.get("results", []):
        idx = int(r.get("row_index", -1))
        if idx < 0 or idx >= len(records):
            continue
        note = records[idx].get(note_col, "")
        kw = _keywords_from_note(str(note))
        if not kw:
            continue
        total += 1
        bundle = " ".join(
            [
                r.get("summary", ""),
                " ".join(str(s) for s in (r.get("suggestions") or [])),
                " ".join(str(e.get("message", "")) for e in (r.get("errors") or [])),
            ]
        )
        if _output_hits_keywords(bundle, kw):
            hits += 1

    hybrid_flags = sum(1 for r in out.get("results", []) if r.get("hybrid_rules_applied"))

    print(f"ملف: {xlsx.name}")
    print(f"صفوف: {len(records)} | نتائج: {len(out.get('results', []))}")
    print(f"صفوف فيها ملاحظة غير فارغة (كلمات مستخرجة للمقارنة): {total}")
    print(f"صفوف طُبّقت فيها قواعد hybrid صريحة: {hybrid_flags}")
    if total:
        print(f"تطابق كلمات من الملاحظة في المخرجات: {hits}/{total} ({100 * hits / total:.1f}%)")
    print(
        "ملاحظة: في وضع fast تكون المخرجات غالباً قواعداً محلية؛ "
        "للمقارنة الدلالية مع الملاحظة شغّل الخادم بمفتاح نموذج لغوي واستخدم mode=smart أو عدّل السكربت."
    )


if __name__ == "__main__":
    asyncio.run(main())
