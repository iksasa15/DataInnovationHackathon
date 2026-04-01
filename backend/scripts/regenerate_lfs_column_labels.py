#!/usr/bin/env python3
"""إعادة توليد backend/data/lfs_column_labels.json من MetaData_LFS_Training_Dataset.xlsx (جذر المستودع)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
_META = _ROOT / "MetaData_LFS_Training_Dataset.xlsx"
_OUT = Path(__file__).resolve().parents[1] / "data" / "lfs_column_labels.json"


def main() -> None:
    if not _META.is_file():
        print(f"غير موجود: {_META}")
        sys.exit(1)
    df = pd.read_excel(_META, sheet_name=0)
    m: dict[str, str] = {}
    for _, r in df.iterrows():
        col = str(r.iloc[0]).strip()
        q = str(r.iloc[1]).strip() if pd.notna(r.iloc[1]) else ""
        if col and col != "Column_Name":
            m[col] = q
    _OUT.parent.mkdir(parents=True, exist_ok=True)
    _OUT.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"تم كتابة {len(m)} تسمية إلى {_OUT}")


if __name__ == "__main__":
    main()
