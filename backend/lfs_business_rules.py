"""
قواعد أعمال صريحة مستوحاة من LFS_Business_Rules.xlsx (طبقة مكمّلة للتحقق الدلالي).
تعمل على صف واحد (قاموس حقول) وتُرجع أخطاء بنفس شكل الـ API.
"""

from __future__ import annotations

import re
from typing import Any


def _age_value(row: dict[str, Any]) -> float | None:
    v = row.get("age")
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _txt(row: dict[str, Any], *keys: str) -> str:
    for k in keys:
        val = row.get(k)
        if val is None:
            continue
        s = str(val).strip()
        if s and s.lower() != "nan":
            return s
    return ""


def _edu_text(row: dict[str, Any]) -> str:
    return _txt(row, "q_301_desc", "q_301")


def _has_secondary_plus(edu: str) -> bool:
    if not edu:
        return False
    patterns = (
        r"ثانوي",
        r"دبلوم",
        r"بكالوريوس",
        r"ماجستير",
        r"دكتوراه",
        r"دكتور",
        r"Secondary",
        r"Diploma",
        r"Bachelor",
        r"Master",
        r"PhD",
    )
    return any(re.search(p, edu, re.I) for p in patterns)


def _has_diploma_plus(edu: str) -> bool:
    if not edu:
        return False
    patterns = (
        r"دبلوم",
        r"بكالوريوس",
        r"ماجستير",
        r"دكتور",
        r"Diploma",
        r"Bachelor",
        r"Master",
        r"PhD",
    )
    return any(re.search(p, edu, re.I) for p in patterns)


def _has_bachelor_plus(edu: str) -> bool:
    if not edu:
        return False
    patterns = (r"بكالوريوس", r"ماجستير", r"دكتور", r"Bachelor", r"Master", r"PhD")
    return any(re.search(p, edu, re.I) for p in patterns)


def _has_master_plus(edu: str) -> bool:
    if not edu:
        return False
    patterns = (r"ماجستير", r"دكتور", r"Master", r"PhD", r"Doctorate")
    return any(re.search(p, edu, re.I) for p in patterns)


def _has_phd_plus(edu: str) -> bool:
    if not edu:
        return False
    patterns = (r"دكتوراه", r"PhD", r"Doctorate", r"دكتور\s*\(")
    return any(re.search(p, edu, re.I) for p in patterns)


def apply_lfs_hybrid_rules(row: dict[str, Any]) -> list[dict[str, Any]]:
    """
    قواعد صلبة تقارب أرقام الأخطاء 2001–2017 في الملف الرسمي (مع تكييف على حقول العمر/المؤهل في مجموعة التدريب).
    """
    errors: list[dict[str, Any]] = []
    age = _age_value(row)
    edu = _edu_text(row)
    rel = _txt(row, "family_relation_desc", "family_relation")
    sector = _txt(row, "q_534_desc", "q_534")
    employer = _txt(row, "q_535_txt", "q_535")
    activity = _txt(row, "q_536_desc", "q_536")

    if age is not None:
        if age < 15 and rel and ("رئيس" in rel or "head" in rel.lower()):
            errors.append(
                {
                    "field": "age",
                    "message": "عمر أقل من 15 مع صلة قرابة تشير إلى رئيس أسرة — خطأ منطقي (قاعدة 2001)",
                    "severity": "high",
                }
            )
        if age < 17 and _has_secondary_plus(edu):
            errors.append(
                {
                    "field": "q_301_desc",
                    "message": "عمر أقل من 17 مع مؤهل ثانوي فأعلى — يتعارض مع قواعد التعليم المعتادة (قاعدة 2011)",
                    "severity": "high",
                }
            )
        if age < 19 and _has_diploma_plus(edu):
            errors.append(
                {
                    "field": "q_301_desc",
                    "message": "عمر أقل من 19 مع دبلوم فأعلى — يستوجب التحقق (قاعدة 2012)",
                    "severity": "high",
                }
            )
        if age < 21 and _has_bachelor_plus(edu):
            errors.append(
                {
                    "field": "q_301_desc",
                    "message": "عمر أقل من 21 مع بكالوريوس فأعلى — تعارض محتمل (قاعدة 2013)",
                    "severity": "medium",
                }
            )
        if age < 23 and _has_master_plus(edu):
            errors.append(
                {
                    "field": "q_301_desc",
                    "message": "عمر أقل من 23 مع ماجستير فأعلى — تعارض محتمل (قاعدة 2015)",
                    "severity": "medium",
                }
            )
        if age < 25 and _has_phd_plus(edu):
            errors.append(
                {
                    "field": "q_301_desc",
                    "message": "عمر أقل من 25 مع دكتوراه — تعارض محتمل (قاعدة 2016)",
                    "severity": "medium",
                }
            )

    # تعارض تخصص/مستوى: ثانوي فقط مع تخصص جامعي (قاعدة 2017 مبسطة)
    hat = edu
    spec = _txt(row, "q_302_e_txt", "q_302")
    if hat and spec and re.search(r"ثانوي|أقل|لم يحصل|بدون", hat, re.I) and re.search(
        r"009|جامع|university|بكالوريوس", spec, re.I
    ):
        errors.append(
            {
                "field": "q_302_e_txt",
                "message": "مستوى تعليم منخفض في q_301 مع تخصص يوحي بمستوى جامعي — تحقق من التوافق (قاعدة 2017)",
                "severity": "high",
            }
        )

    # قطاع عمالة منزلية مقابل نشاط صناعي كبير / كهرباء
    if sector and ("عمالة منزلية" in sector or "domestic" in sector.lower()):
        empl_u = employer.upper()
        act_l = activity.lower()
        if "كهرباء" in employer or "كهرباء" in activity or "electric" in empl_u or "power" in act_l:
            errors.append(
                {
                    "field": "q_534_desc",
                    "message": "قطاع «عمالة منزلية» لا يتسق عادة مع جهة عمل أو نشاط كهرباء/توليد",
                    "severity": "high",
                }
            )

    return errors


def merge_hybrid_into_result(result: dict[str, Any], hybrid_errors: list[dict[str, Any]]) -> dict[str, Any]:
    """دمج أخطاء القواعد الصلبة مع نتيجة النموذج وإعادة حساب الدرجة."""
    if not hybrid_errors:
        return result

    existing = list(result.get("errors") or [])
    fields_seen = {(e.get("field"), e.get("message")) for e in existing if isinstance(e, dict)}

    for e in hybrid_errors:
        key = (e.get("field"), e.get("message"))
        if key not in fields_seen:
            existing.append(e)
            fields_seen.add(key)

    penalty = sum({"high": 35, "medium": 20, "low": 8}.get(str(e.get("severity", "medium")).lower(), 10) for e in existing)
    score = max(0, 100 - penalty)
    if not existing:
        status = "valid"
    elif score >= 50:
        status = "warning"
    else:
        status = "error"

    sug = list(result.get("suggestions") or [])
    if hybrid_errors and "راجع قواعد التحقق الصريحة (طبقة الأعمال)" not in sug:
        sug.insert(0, "راجع قواعد التحقق الصريحة (طبقة الأعمال)")

    summary = str(result.get("summary") or "")
    if hybrid_errors and "طبقة قواعد الأعمال" not in summary:
        summary = (summary + " — رُصدت مخالفات من طبقة قواعد الأعمال.").strip()

    out = {**result, "errors": existing, "confidence_score": score, "status": status, "suggestions": sug[:8], "summary": summary}
    if hybrid_errors:
        out["hybrid_rules_applied"] = True
    return out
