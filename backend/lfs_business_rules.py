"""
قواعد أعمال صريحة مستوحاة من LFS_Business_Rules.xlsx (طبقة مكمّلة للتحقق الدلالي).
تعمل على صف واحد (قاموس حقول) وتُرجع أخطاء بنفس شكل الـ API.
"""

from __future__ import annotations

import re
from typing import Any

from lfs_business_rules_loader import get_rule_record


def _hybrid_rule_error(
    field: str,
    severity: str,
    message_ar: str,
    rule_id: int | None = None,
) -> dict[str, Any]:
    """
    خطأ بتنسيق الـ API؛ يضيف rule_id و message_en من LFS_Business_Rules.xlsx عند التوفر.
    """
    err: dict[str, Any] = {"field": field, "severity": severity, "message": message_ar}
    if rule_id is None:
        return err
    err["rule_id"] = rule_id
    rec = get_rule_record(rule_id)
    if rec:
        en = (rec.get("message_en") or "").strip()
        if en:
            err["message_en"] = en
        et = (rec.get("error_type") or "").strip()
        if et:
            err["rule_type"] = et
    return err


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
                _hybrid_rule_error(
                    "age",
                    "high",
                    "عمر أقل من 15 مع صلة قرابة تشير إلى رئيس أسرة — خطأ منطقي (قاعدة 2001)",
                    2001,
                )
            )
        if age < 17 and _has_secondary_plus(edu):
            errors.append(
                _hybrid_rule_error(
                    "q_301_desc",
                    "high",
                    "عمر أقل من 17 مع مؤهل ثانوي فأعلى — يتعارض مع قواعد التعليم المعتادة (قاعدة 2011)",
                    2011,
                )
            )
        if age < 19 and _has_diploma_plus(edu):
            errors.append(
                _hybrid_rule_error(
                    "q_301_desc",
                    "high",
                    "عمر أقل من 19 مع دبلوم فأعلى — يستوجب التحقق (قاعدة 2012)",
                    2012,
                )
            )
        if age < 21 and _has_bachelor_plus(edu):
            errors.append(
                _hybrid_rule_error(
                    "q_301_desc",
                    "medium",
                    "عمر أقل من 21 مع بكالوريوس فأعلى — تعارض محتمل (قاعدة 2013)",
                    2013,
                )
            )
        if age < 23 and _has_master_plus(edu):
            errors.append(
                _hybrid_rule_error(
                    "q_301_desc",
                    "medium",
                    "عمر أقل من 23 مع ماجستير فأعلى — تعارض محتمل (قاعدة 2015)",
                    2015,
                )
            )
        if age < 25 and _has_phd_plus(edu):
            errors.append(
                _hybrid_rule_error(
                    "q_301_desc",
                    "medium",
                    "عمر أقل من 25 مع دكتوراه — تعارض محتمل (قاعدة 2016)",
                    2016,
                )
            )

    # تعارض تخصص/مستوى: ثانوي فقط مع تخصص جامعي (قاعدة 2017 مبسطة)
    hat = edu
    spec = _txt(row, "q_302_e_txt", "q_302")
    if hat and spec and re.search(r"ثانوي|أقل|لم يحصل|بدون", hat, re.I) and re.search(
        r"009|جامع|university|بكالوريوس", spec, re.I
    ):
        errors.append(
            _hybrid_rule_error(
                "q_302_e_txt",
                "high",
                "مستوى تعليم منخفض في q_301 مع تخصص يوحي بمستوى جامعي — تحقق من التوافق (قاعدة 2017)",
                2017,
            )
        )

    # قطاع عمالة منزلية مقابل نشاط صناعي كبير / كهرباء (قاعدة مكمّلة لمجموعة التدريب — لا يوجد رقم مطابق في كل الحالات)
    if sector and ("عمالة منزلية" in sector or "domestic" in sector.lower()):
        empl_u = employer.upper()
        act_l = activity.lower()
        if "كهرباء" in employer or "كهرباء" in activity or "electric" in empl_u or "power" in act_l:
            errors.append(
                _hybrid_rule_error(
                    "q_534_desc",
                    "high",
                    "قطاع «عمالة منزلية» لا يتسق عادة مع جهة عمل أو نشاط كهرباء/توليد",
                    None,
                )
            )

    return errors


_SPURIOUS_CODE_DESC_MSG = re.compile(
    r"تعارض|متناقض|تناقض\s+بين|لا\s*يتطابق|لا\s*يتسق|"
    r"\bmismatch\b|inconsisten|الرمز\s+و|الكود\s+و|رقم\s+[^\s]+\s+و\s*الوصف|"
    r"\bnumeric\b|code\s+and|وصف\s+لا\s+يت",
    re.I | re.UNICODE,
)


def _pair_base_desc_columns(row: dict[str, Any]) -> list[tuple[str, str]]:
    """أزواج (حقل_رمز، حقل_وصف) مثل gender / gender_desc."""
    out: list[tuple[str, str]] = []
    for k in row:
        if k == "row_index":
            continue
        if isinstance(k, str) and k.endswith("_desc"):
            base = k[:-5]
            if base and base in row:
                out.append((base, k))
    return out


def _nonempty_cell(v: Any) -> bool:
    if v is None:
        return False
    if isinstance(v, float) and v != v:
        return False
    s = str(v).strip()
    return bool(s) and s.lower() != "nan"


def _looks_like_lfs_paired_label(desc: str, base: str) -> bool:
    """تسمية قيمة LFS: غالباً «رقم-نص» أو ذكر/أنثى في حقول التصنيف."""
    t = str(desc).strip()
    if not t:
        return False
    if re.match(r"^\d+\s*[-–]\s*\S", t):
        return True
    if base in ("gender", "nationality", "family_relation", "marage_status") and re.search(
        r"ذكر|أنثى|مؤنث|male|female|سعود|غير", t, re.I
    ):
        return True
    if base.startswith("q_") and re.match(r"^\d+\s*[-–]", t):
        return True
    return False


def strip_code_desc_spurious_errors(errors: list[dict[str, Any]], row: dict[str, Any]) -> list[dict[str, Any]]:
    """
    يزيل أخطاء زائفة تزعم تعارضاً بين حقل رمزي ورقمي وحقل *_desc نصي مرجعي (استبيان LFS).
    ينطبق على كل الأزواج (* / *_desc) وليس فقط الجنس.
    """
    pairs = _pair_base_desc_columns(row)
    if not pairs:
        return errors

    out: list[dict[str, Any]] = []
    for e in errors:
        if not isinstance(e, dict):
            continue
        fld = str(e.get("field", "")).strip()
        msg = str(e.get("message", ""))
        drop = False
        for base, desc_col in pairs:
            if fld not in (base, desc_col):
                continue
            if not _nonempty_cell(row.get(base)) or not _nonempty_cell(row.get(desc_col)):
                continue
            desc_txt = str(row.get(desc_col)).strip()
            if not _looks_like_lfs_paired_label(desc_txt, base):
                continue
            if _SPURIOUS_CODE_DESC_MSG.search(msg):
                drop = True
                break
        if not drop:
            out.append(e)
    return out


def recompute_result_from_errors(result: dict[str, Any], errors: list[dict[str, Any]]) -> dict[str, Any]:
    """إعادة حساب الدرجة والحالة بعد حذف أخطاء."""
    penalty = sum(
        {"high": 35, "medium": 20, "low": 8}.get(str(e.get("severity", "medium")).lower(), 10)
        for e in errors
    )
    score = max(0, 100 - penalty)
    if not errors:
        status = "valid"
    elif score >= 50:
        status = "warning"
    else:
        status = "error"

    out = {
        **result,
        "errors": errors,
        "confidence_score": score,
        "status": status,
    }
    if not errors:
        out["suggestions"] = []
        summ = str(result.get("summary") or "")
        if "تعارض" in summ or "خطأ" in summ or "رُصد" in summ:
            out["summary"] = "البيانات متسقة ومنطقية ضمن حقول الرموز والأوصاف المرجعية."
        else:
            out["summary"] = summ or "البيانات متسقة ومنطقية"
    return out


def apply_code_desc_false_positive_filter(result: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    """يطبّق تصفية أزواج الرمز/الوصف ثم يعيد حساب النتيجة."""
    errs = list(result.get("errors") or [])
    filtered = strip_code_desc_spurious_errors(errs, row)
    if len(filtered) == len(errs):
        return result
    return recompute_result_from_errors(result, filtered)


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
