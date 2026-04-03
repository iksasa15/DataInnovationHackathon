import json
import os
import asyncio
import difflib
import time
from collections import Counter
from typing import Any, Optional

from openai import AsyncOpenAI
import google.generativeai as genai

from prompts import SYSTEM_PROMPT, FEW_SHOT_EXAMPLES

from lfs_business_rules import (
    apply_code_desc_false_positive_filter,
    apply_lfs_hybrid_rules,
    merge_hybrid_into_result,
)
from lfs_metadata import (
    LFS_PRIORITY_COLUMNS,
    load_default_labels,
    max_columns_from_env,
    merge_labels_for_columns,
    select_columns_for_chunk,
    slice_record_to_columns,
)
from prompts_lfs import format_few_shot_lfs_block

# مفتاح Gemini المعيّن من الواجهة (يُفضّل على .env للجلسة الحالية)
_gemini_api_key_override: Optional[str] = None
_gemini_status_cache: Optional[tuple[float, dict]] = None


def _gemini_status_cache_ttl_sec() -> float:
    try:
        return max(15.0, float(os.getenv("GEMINI_STATUS_CACHE_SECONDS", "90")))
    except ValueError:
        return 90.0


def invalidate_gemini_status_cache() -> None:
    global _gemini_status_cache
    _gemini_status_cache = None


def set_gemini_api_key(api_key: Optional[str]) -> None:
    """تعيين مفتاح Gemini من الواجهة (للسيشن الحالي)."""
    global _gemini_api_key_override
    _gemini_api_key_override = (api_key or "").strip() or None
    invalidate_gemini_status_cache()


def get_gemini_api_key() -> str:
    """
    أولوية المفتاح:
    1) التعيين المؤقت من الواجهة (الجلسة)
    2) جدول Supabase app_settings (إن وُجدت الإعدادات)
    3) متغير البيئة GEMINI_API_KEY
    """
    if _gemini_api_key_override:
        return _gemini_api_key_override
    try:
        from supabase_settings import fetch_gemini_api_key_sync, supabase_settings_enabled

        if supabase_settings_enabled():
            k = fetch_gemini_api_key_sync()
            if k:
                return k
    except Exception:
        pass
    return (os.getenv("GEMINI_API_KEY") or "").strip()


def _build_gemini_prompt(form_data: dict) -> str:
    parts = [SYSTEM_PROMPT, "\n\n=== أمثلة تدريبية ===\n"]
    for ex in FEW_SHOT_EXAMPLES:
        parts.append(
            f"\nمثال — مدخلات:\n{json.dumps(ex['input'], ensure_ascii=False, indent=2)}"
            f"\nمثال — ردّ صحيح:\n{json.dumps(ex['output'], ensure_ascii=False, indent=2)}\n"
        )
    parts.append(
        f"\n=== البيانات الجديدة للتحليل ===\n"
        f"{json.dumps(form_data, ensure_ascii=False, indent=2)}\n"
        f"\nاردّ بـ JSON صحيح فقط بدون أي نص إضافي."
    )
    return "".join(parts)


def _build_openai_messages(form_data: dict) -> list[dict]:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for example in FEW_SHOT_EXAMPLES:
        messages.append(
            {
                "role": "user",
                "content": f"حلّل بيانات الاستمارة التالية:\n{json.dumps(example['input'], ensure_ascii=False, indent=2)}",
            }
        )
        messages.append(
            {
                "role": "assistant",
                "content": json.dumps(example["output"], ensure_ascii=False, indent=2),
            }
        )
    messages.append(
        {
            "role": "user",
            "content": f"حلّل بيانات الاستمارة التالية:\n{json.dumps(form_data, ensure_ascii=False, indent=2)}",
        }
    )
    return messages


def _gemini_models() -> list[str]:
    return [
        "gemini-2.0-flash-lite",
        "gemini-2.5-flash-lite",
        "gemini-flash-lite-latest",
        "gemini-2.0-flash",
        "gemini-2.5-flash",
        "gemini-flash-latest",
    ]


async def _call_gemini_prompt(prompt: str) -> dict:
    api_key = get_gemini_api_key()
    genai.configure(api_key=api_key)

    last_exc = None
    for i, model_name in enumerate(_gemini_models()):
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )
            response = await asyncio.to_thread(model.generate_content, prompt)
            content = (response.text or "{}").strip()
            return json.loads(content)
        except Exception as exc:
            last_exc = exc
            err = str(exc).lower()
            is_quota = "429" in err or "quota" in err or "rate" in err
            is_not_found = "404" in err or "not found" in err
            if is_not_found:
                continue
            if is_quota and i < len(_gemini_models()) - 1:
                await asyncio.sleep(1)
                continue
            break

    raise last_exc


async def _call_gemini(form_data: dict) -> dict:
    return await _call_gemini_prompt(_build_gemini_prompt(form_data))


async def check_gemini_connection() -> dict:
    """التحقق من اتصال Gemini بعمل طلب بسيط. النتيجة تُخزَّن مؤقتاً لتقليل استهلاك الحصة."""
    global _gemini_status_cache

    api_key = get_gemini_api_key()
    if not api_key:
        return {"ok": False, "message": "مفتاح GEMINI_API_KEY غير مضبوط في .env"}

    now = time.time()
    ttl = _gemini_status_cache_ttl_sec()
    if _gemini_status_cache and (now - _gemini_status_cache[0]) < ttl:
        out = dict(_gemini_status_cache[1])
        out["cached"] = True
        return out

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name=_gemini_models()[0],
            generation_config=genai.GenerationConfig(temperature=0, max_output_tokens=10),
        )
        response = await asyncio.to_thread(model.generate_content, "قل: متصل")
        if response and response.text:
            result = {"ok": True, "message": "متصل بـ Gemini بنجاح"}
        else:
            result = {"ok": True, "message": "تم الاتصال"}
        _gemini_status_cache = (now, {k: v for k, v in result.items() if k != "cached"})
        return result
    except Exception as exc:
        err = str(exc).lower()
        if "api_key" in err or "invalid" in err or "401" in err:
            result = {"ok": False, "message": "مفتاح API غير صالح أو منتهي"}
        elif "429" in err or "quota" in err or "rate" in err:
            result = {
                "ok": False,
                "message": "تجاوز حد الاستخدام (Google). انتظر ساعات أو راجع الحصة في AI Studio — لا تكرر الطلب كثيراً.",
            }
        elif "network" in err or "connection" in err:
            result = {"ok": False, "message": "فشل الاتصال بالشبكة"}
        else:
            result = {"ok": False, "message": f"خطأ: {str(exc)[:120]}"}
        _gemini_status_cache = (now, result)
        return result


async def _call_openai_compatible(form_data: dict, base_url: str, api_key: str, model: str) -> dict:
    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    messages = _build_openai_messages(form_data)
    response = await client.chat.completions.create(
        model=model,
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.1,
        max_tokens=1200,
    )
    return json.loads(response.choices[0].message.content)


def _form_payload_to_hybrid_row(data: dict[str, Any]) -> dict[str, Any]:
    """
    يحوّل حقول الاستمارة المبسّطة (education, sector, …) إلى أسماء أعمدة LFS
    التي يتوقعها apply_lfs_hybrid_rules (q_301, q_534, …).
    """
    row: dict[str, Any] = dict(data)
    edu = row.get("education")
    if edu is not None and str(edu).strip() != "":
        row.setdefault("q_301", edu)
    jt = row.get("job_title")
    if jt is not None and str(jt).strip() != "":
        row.setdefault("q_537_e_job", jt)
    ms = row.get("monthly_salary")
    if ms is not None and ms != "" and ms != 0:
        row.setdefault("q_602_val", ms)
    sec = row.get("sector")
    if sec is not None and str(sec).strip() != "":
        row.setdefault("q_534", sec)
    mar = row.get("marital_status")
    if mar is not None and str(mar).strip() != "":
        row.setdefault("marage_status", mar)
    return row


async def validate_form(raw_data: dict) -> dict:
    data = dict(raw_data)
    use_llm = bool(data.pop("use_llm", True))
    apply_hybrid = bool(data.pop("apply_hybrid_rules", True))

    clean = {k: v for k, v in data.items() if v is not None and v != "" and v != 0 and k != "name"}

    if len(clean) < 2:
        return _empty_result()

    hybrid_row = _form_payload_to_hybrid_row(data)

    # قواعد الأعمال فقط — بلا نموذج لغوي (مثل Excel: use_llm=False)
    if not use_llm:
        base: dict[str, Any] = {
            "confidence_score": 100,
            "status": "valid",
            "errors": [],
            "suggestions": [],
            "summary": "تحليل بقواعد الأعمال فقط — لم يُستدعَ نموذج لغوي.",
        }
        if apply_hybrid:
            merged = merge_hybrid_into_result(base, apply_lfs_hybrid_rules(hybrid_row))
            return apply_code_desc_false_positive_filter(merged, hybrid_row)
        base["summary"] = "لم يُفعّل لا التحليل الذكي ولا قواعد الأعمال — اختر «قواعد الأعمال» أو «الكل»."
        return base

    gemini_key = get_gemini_api_key()
    groq_key = os.getenv("GROQ_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    try:
        if gemini_key:
            result = await _call_gemini(clean)
        elif groq_key:
            result = await _call_openai_compatible(
                clean,
                base_url="https://api.groq.com/openai/v1",
                api_key=groq_key,
                model="llama-3.3-70b-versatile",
            )
        elif openai_key:
            result = await _call_openai_compatible(
                clean,
                base_url="https://api.openai.com/v1",
                api_key=openai_key,
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            )
        else:
            result = _mock_validate(clean)

        if apply_hybrid:
            result = merge_hybrid_into_result(result, apply_lfs_hybrid_rules(hybrid_row))
        return apply_code_desc_false_positive_filter(result, hybrid_row)

    except Exception:
        result = _mock_validate(clean)
        if apply_hybrid:
            result = merge_hybrid_into_result(result, apply_lfs_hybrid_rules(hybrid_row))
        return apply_code_desc_false_positive_filter(result, hybrid_row)


# ---------- Dynamic batch validation for arbitrary Excel forms ----------

def _norm_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower().replace("_", " ").replace("-", " ")


def _map_field_to_columns(field: str, columns: list[str]) -> str:
    if not field:
        return ""
    if field in columns:
        return field

    target = _norm_text(field)
    col_by_norm = {_norm_text(c): c for c in columns}

    if target in col_by_norm:
        return col_by_norm[target]

    for norm_col, original in col_by_norm.items():
        if target in norm_col or norm_col in target:
            return original

    matches = difflib.get_close_matches(target, list(col_by_norm.keys()), n=1, cutoff=0.72)
    if matches:
        return col_by_norm[matches[0]]

    return field


def _sanitize_dynamic_item(item: dict, row_index: int, columns: list[str]) -> dict:
    errors_in = item.get("errors") if isinstance(item.get("errors"), list) else []
    errors = []

    for err in errors_in:
        if not isinstance(err, dict):
            continue
        mapped_field = _map_field_to_columns(str(err.get("field", "")).strip(), columns)
        severity = str(err.get("severity", "medium")).lower()
        if severity not in {"low", "medium", "high"}:
            severity = "medium"
        message = str(err.get("message", "")).strip()
        if not message:
            continue
        errors.append(
            {
                "field": mapped_field,
                "message": message,
                "severity": severity,
            }
        )

    score = item.get("confidence_score", 100)
    try:
        score = int(round(float(score)))
    except Exception:
        score = 100
    score = max(0, min(100, score))

    status = str(item.get("status", "")).lower().strip()
    if status not in {"valid", "warning", "error"}:
        if not errors:
            status = "valid"
        elif score >= 50:
            status = "warning"
        else:
            status = "error"

    suggestions = item.get("suggestions") if isinstance(item.get("suggestions"), list) else []
    suggestions = [str(s) for s in suggestions if str(s).strip()][:5]

    summary = str(item.get("summary", "")).strip()
    if not summary:
        summary = "البيانات متسقة ومنطقية" if not errors else f"رُصد {len(errors)} تعارضات تحتاج مراجعة"

    return {
        "row_index": row_index,
        "confidence_score": score,
        "status": status,
        "errors": errors,
        "suggestions": suggestions,
        "summary": summary,
    }


def _compute_stats(results: list[dict]) -> dict:
    total = len(results)
    errors_count = sum(1 for r in results if r.get("status") == "error")
    warnings_count = sum(1 for r in results if r.get("status") == "warning")
    avg_confidence = round(sum(int(r.get("confidence_score", 0)) for r in results) / total) if total else 0
    return {
        "total": total,
        "errors": errors_count,
        "warnings": warnings_count,
        "valid": total - errors_count - warnings_count,
        "avg_confidence": avg_confidence,
    }


def _baseline_row_result(row_index: int) -> dict:
    """نتيجة افتراضية قبل دمج قواعد الأعمال فقط (بدون نموذج لغوي)."""
    return {
        "row_index": row_index,
        "confidence_score": 100,
        "status": "valid",
        "errors": [],
        "suggestions": [],
        "summary": "تحليل بقواعد الأعمال فقط — لم يُستدعَ نموذج لغوي.",
    }


def _is_missing_value(value: Any) -> bool:
    """هل القيمة تعتبر مفقودة (فارغة أو غير صالحة للتحليل)."""
    if value is None:
        return True
    if isinstance(value, (int, float)):
        if isinstance(value, float) and value != value:  # NaN
            return True
        return False  # 0 أو أي عدد نعتبره موجوداً
    return not str(value).strip()


def _is_important_column(col_norm: str) -> bool:
    """حقول يُفضّل عدم تركها فارغة في الاستبيان."""
    keywords = (
        "اسم", "عمر", "سن", "age", "مسمى", "وظيف", "job", "مؤهل", "تعليم", "education",
        "راتب", "salary", "خبرة", "experience", "جنس", "gender", "حالة", "اجتماع", "marital",
        "قطاع", "sector", "أبناء", "تابع", "children"
    )
    return any(kw in col_norm for kw in keywords)


def _dynamic_fallback(columns: list[str], records: list[dict]) -> dict:
    results = []
    for rec in records:
        row_index = int(rec.get("row_index", 0))
        errors = []
        suggestions = []
        col_norms = {col: _norm_text(col) for col in columns}

        # معالج القيم المفقودة: رصد الحقول المهمة الفارغة وإضافة اقتراح استكمال
        for col in columns:
            value = rec.get(col)
            col_norm = col_norms[col]
            if _is_missing_value(value) and _is_important_column(col_norm):
                errors.append(
                    {
                        "field": col,
                        "message": f"القيمة مفقودة في الحقل «{col}»",
                        "severity": "medium",
                    }
                )
                suggestions.append(f"أكمل حقل «{col}» بقيمة مناسبة")

        for col in columns:
            value = rec.get(col)
            col_norm = col_norms[col]

            if isinstance(value, (int, float)):
                if value is None or (isinstance(value, float) and value != value):
                    continue
                if ("عمر" in col_norm or "سن" in col_norm or "age" in col_norm) and (value < 0 or value > 100):
                    errors.append(
                        {"field": col, "message": f"القيمة ({value}) في '{col}' غير منطقية", "severity": "high"}
                    )
                    suggestions.append(f"صحّح حقل «{col}» ليكون بين 0 و 100")
                elif value < 0:
                    errors.append(
                        {"field": col, "message": f"القيمة ({value}) في '{col}' سالبة", "severity": "medium"}
                    )
                    suggestions.append(f"صحّح قيمة «{col}» لتكون عدداً موجباً")
                elif abs(value) > 1_000_000_000:
                    errors.append(
                        {"field": col, "message": f"القيمة في '{col}' كبيرة جداً وقد تكون خطأ", "severity": "high"}
                    )
                    suggestions.append(f"راجع قيمة «{col}» — قد يكون هناك خطأ إدخال (مثل فواصل أو وحدات)")
                continue

            value_str = str(value).strip() if value is not None else ""
            if not value_str:
                continue

            # تسميات ومتناسقها مع حقول أخرى
            if "مؤهل" in col_norm or "تعليم" in col_norm or "شهادة" in col_norm:
                job_col = next((c for c in columns if "مسمى" in col_norms[c] or "وظيف" in col_norms[c]), None)
                if job_col:
                    job = str(rec.get(job_col) or "").strip()
                    low_edu = ["ابتدائي", "متوسط", "إعدادي", "ثانوي", "دبلوم"]
                    if any(e in value_str for e in low_edu) and any(
                        t in job for t in ["طبيب", "دكتور", "جراح", "طيار", "وزير", "مدير عام", "قاضي"]
                    ):
                        errors.append(
                            {
                                "field": col,
                                "message": f"المؤهل «{value_str}» لا يتناسب مع المسمى الوظيفي «{job}»",
                                "severity": "high",
                            }
                        )
                        suggestions.append("راجع المؤهل العلمي أو المسمى الوظيفي ليتناسبا مع بعضهما")
            if "مسمى" in col_norm or "وظيف" in col_norm:
                edu_col = next((c for c in columns if "مؤهل" in col_norms[c] or "تعليم" in col_norms[c]), None)
                if edu_col:
                    edu = str(rec.get(edu_col) or "").strip()
                    low_edu = ["ابتدائي", "متوسط", "إعدادي", "دبلوم"]
                    if any(e in edu for e in low_edu) and any(
                        t in value_str for t in ["طبيب", "دكتور", "جراح", "طيار", "وزير", "قاضي"]
                    ):
                        errors.append(
                            {
                                "field": col,
                                "message": f"المسمى «{value_str}» لا يتناسب مع المؤهل «{edu}»",
                                "severity": "high",
                            }
                        )
                        suggestions.append("راجع المسمى الوظيفي أو المؤهل العلمي ليتوافقا مع بعضهما")
            if "حالة" in col_norm and "اجتماع" in col_norm:
                if "أعزب" in value_str or "عزب" in value_str:
                    children_col = next(
                        (c for c in columns if "تابع" in col_norms[c] or "أبناء" in col_norms[c] or "أولاد" in col_norms[c]),
                        None,
                    )
                    if children_col is not None:
                        try:
                            n = int(float(rec.get(children_col) or 0))
                            if n > 0:
                                errors.append(
                                    {
                                        "field": col,
                                        "message": f"الحالة «{value_str}» مع وجود تابعين/أبناء يستوجب التحقق",
                                        "severity": "medium",
                                    }
                                )
                                suggestions.append("تحقق من الحالة الاجتماعية وعدد الأبناء مع المستجيب")
                        except (TypeError, ValueError):
                            pass

        penalty = sum({"high": 35, "medium": 20, "low": 8}.get(e["severity"], 10) for e in errors)
        score = max(0, 100 - penalty)
        status = "valid" if not errors else ("warning" if score >= 50 else "error")
        if not suggestions and errors:
            suggestions = ["راجع الحقول المميزة في هذا الصف"]
        suggestions = list(dict.fromkeys(suggestions))[:6]  # إزالة التكرار وحد أقصى 6
        results.append(
            {
                "row_index": row_index,
                "confidence_score": score,
                "status": status,
                "errors": errors,
                "suggestions": suggestions,
                "summary": "البيانات تبدو منطقية" if not errors else f"رُصد {len(errors)} تعارضات/قيم مفقودة محتملة",
            }
        )

    return {"results": results, "stats": _compute_stats(results)}


def _build_dynamic_batch_prompt(
    columns: list[str],
    records_chunk: list[dict],
    column_labels: Optional[dict[str, str]] = None,
    include_lfs_few_shot: bool = True,
) -> str:
    labels_section = ""
    if column_labels:
        slim = {c: column_labels[c] for c in columns if c in column_labels}
        if slim:
            labels_section = (
                "\nقاموس معاني الحقول (مرجع — استخدم أسماء الأعمدة كما هي في الأخطاء):\n"
                f"{json.dumps(slim, ensure_ascii=False, indent=2)}\n"
            )
    few_lfs = format_few_shot_lfs_block() if include_lfs_few_shot else ""

    return (
        "أنت مدقق جودة بيانات خبير في اكتشاف التناقضات المنطقية والدلالية في أي نموذج استبيان.\n"
        "مهم: جميع المخرجات (message في errors، suggestions، summary) يجب أن تكون باللغة العربية فقط، حتى لو كانت البيانات المدخلة بالإنجليزية أو بأي لغة أخرى.\n"
        "حلّل كل صف اعتماداً على العلاقة بين الحقول داخل نفس الصف فقط.\n"
        f"{few_lfs}"
        f"{labels_section}"
        "المطلوب — تحليل كل شيء وليس الأرقام فقط:\n"
        "• الأرقام: عمر، رواتب، سنوات خبرة، أعداد — تحقق من المنطق والحدود.\n"
        "• النصوص والتسميات: المسمى الوظيفي، المؤهل العلمي، الحالة الاجتماعية، نوع السكن، جهة العمل، أي تسمية أو تصنيف — تحقق من التناسق بينها (مثلاً مؤهل «ابتدائي» مع مسمى «طبيب»، أو «أعزب» مع «عدد أبناء» كبير، أو عمر صغير مع منصب قيادي).\n"
        "• أزواج حقول استبيان LFS (مهم جداً): إذا وُجد حقل اسمه «X» مع حقل «X_desc» (مثل gender مع gender_desc، nationality مع nationality_desc، q_301 مع q_301_desc، وأي q_* مع q_*_desc)، "
        "فالأول غالباً **رمز أو رقم معرف** من الجدول، والثاني **وصف نصي مرجعي** من الاستمارة (غالباً بصيغة «رقم-نص» مثل «1-ذكر» أو «2-أنثى»). "
        "**لا تعتبر ذلك تعارضاً أو تناقضاً** بين الرقم والنص — هما مكملان من نظام الترميز. لا تُسجّل خطأ يدّعي عدم تطابق الرمز مع الوصف لهذه الأزواج.\n"
        "• أي حقل آخر: أسماء، فئات، تواريخ، نصوص حرة — راعِ التناسق مع باقي حقول نفس الصف.\n\n"
        "معالج القيم المفقودة والأخطاء:\n"
        "• القيمة المفقودة: إذا كان حقل مهماً فارغاً أو غير مكتمل، أضفه في errors بشدة مناسبة (مثلاً severity: \"medium\") مع message يوضح أن القيمة مفقودة، وفي suggestions أضف اقتراحاً لاستكماله (مثل: \"أكمل حقل [اسم الحقل] بقيمة مناسبة\").\n"
        "• الحقول التي فيها أخطاء: لكل خطأ في errors قدّم في suggestions اقتراحاً واضحاً لتعديل القيمة أو تصحيحها (مثلاً: \"صحّح العمر ليكون متناسقاً مع سنوات الخبرة\" أو \"راجع المؤهل العلمي ليتوافق مع المسمى الوظيفي\").\n"
        "• الاقتراحات: يجب أن تكون عملية وقابلة للتطبيق — أي تخبر المستخدم ماذا يفعل لمعالجة المشكلة أو القيمة المفقودة.\n\n"
        "1) اكتشاف القيم المفقودة (حقول فارغة أو شبه فارغة) واعتبارها مشكلة مع اقتراح استكمال.\n"
        "2) اكتشاف القيم غير المنطقية أو المتناقضة سياقياً في كل الحقول.\n"
        "3) إرجاع الأخطاء على مستوى الحقول مع ذكر اسم الحقل كما هو EXACT من قائمة الأعمدة.\n"
        "4) إرجاع suggestions تحتوي دائماً اقتراحات للتعديل أو استكمال القيم المفقودة.\n"
        "5) إرجاع درجة ثقة لكل صف من 0 إلى 100.\n\n"
        "قائمة الأعمدة (استخدم الأسماء كما هي دون ترجمة):\n"
        f"{json.dumps(columns, ensure_ascii=False)}\n\n"
        "الصفوف للتحليل:\n"
        f"{json.dumps(records_chunk, ensure_ascii=False)}\n\n"
        "أعد JSON فقط بهذه البنية:\n"
        "{\n"
        '  "results": [\n'
        "    {\n"
        '      "row_index": 0,\n'
        '      "confidence_score": 0,\n'
        '      "status": "valid|warning|error",\n'
        '      "errors": [\n'
        "        {\n"
        '          "field": "<اسم عمود من القائمة كما هو>",\n'
        '          "message": "<سبب التعارض أو وصف القيمة المفقودة>",\n'
        '          "severity": "low|medium|high"\n'
        "        }\n"
        "      ],\n"
        '      "suggestions": ["<اقتراح تعديل أو استكمال قيمة مفقودة 1>", "..."],\n'
        '      "summary": "..."\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "تأكد من شمول كل row_index في الرد، حتى إن لم يوجد خطأ (errors = [])."
    )


async def validate_rows_dynamic(
    columns: list[str],
    records: list[dict],
    mode: str = "smart",
    *,
    column_labels: Optional[dict[str, str]] = None,
    embed_metadata: bool = True,
    column_subset: bool = True,
    max_columns: Optional[int] = None,
    apply_hybrid_rules: bool = True,
    use_llm: bool = True,
) -> dict:
    if not columns or not records:
        return {"results": [], "stats": _compute_stats([]), "provider": "local"}

    cleaned_records = []
    for rec in records:
        if not isinstance(rec, dict):
            continue
        row_index = rec.get("row_index")
        if row_index is None:
            continue
        clean_row = {"row_index": int(row_index)}
        for col in columns:
            clean_row[col] = rec.get(col)
        cleaned_records.append(clean_row)

    if not cleaned_records:
        return {"results": [], "stats": _compute_stats([]), "provider": "local"}

    # قواعد الأعمال فقط — بدون Gemini ولا التحقق المحلي الموسّع
    if not use_llm:
        rules_results: list[dict] = []
        for rec in cleaned_records:
            idx = int(rec["row_index"])
            base = _baseline_row_result(idx)
            if apply_hybrid_rules:
                merged = merge_hybrid_into_result(base, apply_lfs_hybrid_rules(rec))
                merged = apply_code_desc_false_positive_filter(merged, rec)
            else:
                merged = base
                merged["summary"] = "لم يُفعّل تحليل ولا قواعد — الصف سليم افتراضياً."
            rules_results.append(merged)
        return {
            "results": rules_results,
            "stats": _compute_stats(rules_results),
            "provider": "rules",
        }

    default_labs = load_default_labels() if embed_metadata else {}

    mc = max_columns if max_columns is not None else max_columns_from_env()

    mode = (mode or "smart").lower().strip()
    if mode == "fast":
        out = _dynamic_fallback(columns, cleaned_records)
        out["provider"] = "local"
        results_fast = []
        for r in out["results"]:
            idx = int(r.get("row_index", 0))
            full = next((cr for cr in cleaned_records if int(cr["row_index"]) == idx), None)
            if full:
                r = apply_code_desc_false_positive_filter(r, full)
            if apply_hybrid_rules and full:
                r = merge_hybrid_into_result(r, apply_lfs_hybrid_rules(full))
            results_fast.append(r)
        out["results"] = results_fast
        out["stats"] = _compute_stats(results_fast)
        return out

    gemini_key = get_gemini_api_key()
    if not gemini_key:
        out = _dynamic_fallback(columns, cleaned_records)
        out["provider"] = "local"
        out["gemini_unavailable"] = True
        results_local = []
        for r in out["results"]:
            idx = int(r.get("row_index", 0))
            full = next((cr for cr in cleaned_records if int(cr["row_index"]) == idx), None)
            if full:
                r = apply_code_desc_false_positive_filter(r, full)
            if apply_hybrid_rules and full:
                r = merge_hybrid_into_result(r, apply_lfs_hybrid_rules(full))
            results_local.append(r)
        out["results"] = results_local
        out["stats"] = _compute_stats(results_local)
        return out

    chunk_size = max(5, int(os.getenv("DYNAMIC_BATCH_SIZE", "20")))
    results = []
    gemini_used = False

    for i in range(0, len(cleaned_records), chunk_size):
        chunk_full = cleaned_records[i : i + chunk_size]
        cols_use = (
            select_columns_for_chunk(columns, chunk_full, LFS_PRIORITY_COLUMNS, mc)
            if column_subset
            else columns
        )
        labels_for_prompt = merge_labels_for_columns(cols_use, default_labs, column_labels)
        chunk_llm = [slice_record_to_columns(rec, cols_use) for rec in chunk_full]
        try:
            prompt = _build_dynamic_batch_prompt(
                cols_use,
                chunk_llm,
                column_labels=labels_for_prompt,
                include_lfs_few_shot=True,
            )
            raw = await _call_gemini_prompt(prompt)
            model_results = raw.get("results") if isinstance(raw, dict) else []
            model_results = model_results if isinstance(model_results, list) else []

            by_index = {}
            for item in model_results:
                if isinstance(item, dict) and "row_index" in item:
                    by_index[int(item["row_index"])] = item

            for rec_full in chunk_full:
                idx = int(rec_full["row_index"])
                item = by_index.get(idx, {})
                sanitized = _sanitize_dynamic_item(item, idx, cols_use)
                sanitized = apply_code_desc_false_positive_filter(sanitized, rec_full)
                if apply_hybrid_rules:
                    sanitized = merge_hybrid_into_result(sanitized, apply_lfs_hybrid_rules(rec_full))
                results.append(sanitized)
            gemini_used = True
        except Exception:
            fallback_chunk = _dynamic_fallback(cols_use, chunk_llm)
            for fb in fallback_chunk["results"]:
                idx = int(fb.get("row_index", 0))
                full = next((cr for cr in chunk_full if int(cr["row_index"]) == idx), None)
                if full:
                    fb = apply_code_desc_false_positive_filter(fb, full)
                if apply_hybrid_rules and full:
                    fb = merge_hybrid_into_result(fb, apply_lfs_hybrid_rules(full))
                results.append(fb)

    results.sort(key=lambda r: int(r.get("row_index", 0)))
    return {
        "results": results,
        "stats": _compute_stats(results),
        "provider": "gemini" if gemini_used else "local",
    }


def validate_form_quick(data: dict) -> dict:
    """تحقق فوري بالقواعد — للمعالجة الدفعية بدون مفتاح LLM؛ يدعم use_llm / apply_hybrid_rules كـ validate_form."""
    d = dict(data)
    use_llm = bool(d.pop("use_llm", True))
    apply_hybrid = bool(d.pop("apply_hybrid_rules", True))
    clean = {k: v for k, v in d.items() if v is not None and v != "" and v != 0 and k != "name"}
    if len(clean) < 2:
        return _empty_result()
    hybrid_row = _form_payload_to_hybrid_row(d)

    if not use_llm:
        base: dict[str, Any] = {
            "confidence_score": 100,
            "status": "valid",
            "errors": [],
            "suggestions": [],
            "summary": "تحليل بقواعد الأعمال فقط — لم يُستدعَ نموذج لغوي.",
        }
        if apply_hybrid:
            merged = merge_hybrid_into_result(base, apply_lfs_hybrid_rules(hybrid_row))
            return apply_code_desc_false_positive_filter(merged, hybrid_row)
        base["summary"] = "لم يُفعّل لا التحليل الذكي ولا قواعد الأعمال — اختر «قواعد الأعمال» أو «الكل»."
        return base

    result = _mock_validate(clean)
    if apply_hybrid:
        result = merge_hybrid_into_result(result, apply_lfs_hybrid_rules(hybrid_row))
    return apply_code_desc_false_positive_filter(result, hybrid_row)


def _empty_result() -> dict:
    return {
        "confidence_score": 100,
        "status": "valid",
        "errors": [],
        "suggestions": [],
        "summary": "أدخل بيانات كافية لبدء التحقق التلقائي",
    }


def _mock_validate(data: dict) -> dict:
    """
    وضع تجريبي يعمل بقواعد ثابتة عندما لا يكون مفتاح API متاحاً.
    يُظهر قدرات النظام للعرض التوضيحي.
    """
    errors = []

    age = data.get("age")
    years_exp = data.get("years_experience")
    education = data.get("education", "")
    job_title = data.get("job_title", "")
    marital = data.get("marital_status", "")
    children = data.get("children_count", 0) or 0
    salary = data.get("monthly_salary", 0) or 0

    medical_jobs = ["طبيب", "طبيبة", "دكتور", "دكتورة", "صيدلاني", "صيدلانية"]
    engineer_jobs = ["مهندس", "مهندسة"]
    executive_jobs = ["مدير عام", "رئيس تنفيذي", "نائب رئيس"]
    low_edu = ["ابتدائي", "متوسط", "إعدادي"]
    diploma_edu = ["دبلوم", "ثانوي"]

    if age and years_exp:
        max_possible_exp = age - 15
        if years_exp > max_possible_exp:
            errors.append(
                {
                    "field": "years_experience",
                    "message": f"سنوات الخبرة ({years_exp}) غير منطقية مع العمر ({age}) — الحد الأقصى المعقول هو {max(0, max_possible_exp)} سنة",
                    "severity": "high",
                }
            )

    if job_title:
        if any(j in job_title for j in medical_jobs) and education in low_edu + diploma_edu:
            errors.append(
                {
                    "field": "education",
                    "message": f"'{job_title}' يتطلب بكالوريوس على الأقل — المؤهل '{education}' لا يؤهل لممارسة المهنة الطبية",
                    "severity": "high",
                }
            )
        elif any(j in job_title for j in engineer_jobs) and education in low_edu:
            errors.append(
                {
                    "field": "education",
                    "message": f"'{job_title}' يتطلب بكالوريوس هندسة على الأقل — المؤهل الحالي غير كافٍ",
                    "severity": "high",
                }
            )
        elif any(j in job_title for j in executive_jobs):
            if age and age < 30:
                errors.append(
                    {
                        "field": "job_title",
                        "message": f"منصب '{job_title}' نادراً ما يُشغله شخص دون الثلاثين — تحقق من صحة المسمى",
                        "severity": "medium",
                    }
                )
            if years_exp is not None and years_exp < 8:
                errors.append(
                    {
                        "field": "years_experience",
                        "message": f"منصب '{job_title}' عادةً يستلزم خبرة 10 سنوات فأكثر",
                        "severity": "medium",
                    }
                )

    if children > 0 and marital == "أعزب":
        errors.append(
            {
                "field": "children_count",
                "message": f"وجود {children} أبناء مع الحالة الاجتماعية 'أعزب' يستوجب التحقق من المستجيب",
                "severity": "medium",
            }
        )

    if salary and salary > 0:
        if job_title and any(j in job_title for j in ["موظف", "موظفة", "سائق", "عامل"]) and salary > 50000:
            errors.append(
                {
                    "field": "monthly_salary",
                    "message": f"الراتب ({salary:,.0f} ر.س) مرتفع جداً بالنسبة لمسمى '{job_title}'",
                    "severity": "low",
                }
            )

    penalty = sum({"high": 35, "medium": 20, "low": 8}.get(e["severity"], 10) for e in errors)
    confidence = max(0, 100 - penalty)

    if not errors:
        status = "valid"
    elif confidence >= 50:
        status = "warning"
    else:
        status = "error"

    suggestions = []
    if errors:
        fields = {e["field"] for e in errors}
        if "years_experience" in fields or "age" in fields:
            suggestions.append("راجع حقلَي العمر وسنوات الخبرة مع المستجيب مباشرةً")
        if "education" in fields:
            suggestions.append("تحقق من الشهادة الفعلية وطلب صورة منها إن أمكن")
        if "job_title" in fields:
            suggestions.append("اطلب من المستجيب توضيح مسماه الوظيفي الدقيق")

    summary = "البيانات متسقة ومنطقية — لا توجد تعارضات مرصودة." if not errors else f"رُصد {len(errors)} تعارضات تستوجب المراجعة."

    return {
        "confidence_score": confidence,
        "status": status,
        "errors": errors,
        "suggestions": suggestions,
        "summary": summary,
    }


def aggregate_dynamic_batch_errors(results: list[dict]) -> dict[str, Any]:
    """تجميع أخطاء الدفعة: تكرار (حقل + رسالة)، حقول بأكثر/أقل إشارات."""
    pair_counts: Counter[tuple[str, str]] = Counter()
    severity_by_pair: dict[tuple[str, str], str] = {}

    for r in results:
        if not isinstance(r, dict):
            continue
        for e in r.get("errors") or []:
            if not isinstance(e, dict):
                continue
            field = str(e.get("field", "") or "?").strip() or "?"
            msg = str(e.get("message", "") or "").strip()
            if len(msg) > 1500:
                msg = msg[:1500] + "…"
            key = (field, msg)
            pair_counts[key] += 1
            sev = str(e.get("severity", "medium")).lower()
            if key not in severity_by_pair or sev == "high":
                severity_by_pair[key] = sev

    most_repeated = [
        {
            "field": k[0],
            "message": k[1],
            "count": c,
            "severity": severity_by_pair.get(k, "medium"),
        }
        for k, c in pair_counts.most_common(40)
    ]
    singleton_keys = [k for k, c in pair_counts.items() if c == 1]
    rare_singletons_sample = [{"field": k[0], "message": k[1], "count": 1} for k in singleton_keys[:45]]

    field_counts: Counter[str] = Counter()
    for (f, _), c in pair_counts.items():
        field_counts[f] += c

    fields_desc = [{"field": f, "error_mentions": n} for f, n in field_counts.most_common(30)]
    fields_asc = sorted(field_counts.items(), key=lambda x: (x[1], x[0]))
    fields_least = [{"field": f, "error_mentions": n} for f, n in fields_asc[:25]]

    return {
        "total_error_occurrences": int(sum(pair_counts.values())),
        "unique_error_types": len(pair_counts),
        "singleton_count": len(singleton_keys),
        "most_repeated": most_repeated,
        "rare_singletons_sample": rare_singletons_sample,
        "fields_by_errors_desc": fields_desc,
        "fields_by_errors_asc": fields_least,
    }


def _normalize_insight_report(raw: dict[str, Any]) -> dict[str, Any]:
    rec = raw.get("recommendations_ar")
    if not isinstance(rec, list):
        rec = []
    pri = raw.get("priority_fields_ar")
    if not isinstance(pri, list):
        pri = []
    return {
        "summary_ar": str(raw.get("summary_ar", "") or "").strip(),
        "most_repeated_insights_ar": str(raw.get("most_repeated_insights_ar", "") or "").strip(),
        "rare_and_isolated_ar": str(raw.get("rare_and_isolated_ar", "") or "").strip(),
        "least_problematic_fields_ar": str(raw.get("least_problematic_fields_ar", "") or "").strip(),
        "recommendations_ar": [str(x).strip() for x in rec if str(x).strip()],
        "priority_fields_ar": [str(x).strip() for x in pri if str(x).strip()],
    }


def _fallback_insights_report_ar(stats: dict[str, Any], agg: dict[str, Any]) -> dict[str, Any]:
    """تقرير عربي من الإحصاءات فقط (بدون LLM)."""
    st = stats or {}
    total = int(st.get("total", 0) or 0)
    err_rows = int(st.get("errors", 0) or 0)
    warn_rows = int(st.get("warnings", 0) or 0)
    valid_rows = int(st.get("valid", 0) or 0)
    avg_c = int(st.get("avg_confidence", 0) or 0)

    head = (
        f"من أصل {total} سجلًا: صفوف بخطأ {err_rows}، تحذيرات {warn_rows}، سليمة {valid_rows}، "
        f"ومتوسط درجة الثقة {avg_c}%."
    )

    if agg.get("total_error_occurrences", 0) == 0:
        return {
            "summary_ar": head + " لم تُسجَّل أخطاء على مستوى الحقول في تفاصيل الصفوف.",
            "most_repeated_insights_ar": "لا توجد أنماط أخطاء متكررة — إما عدم وجود أخطاء حقلية أو أن التحليل لم يُرجع تفاصيل.",
            "rare_and_isolated_ar": "لا توجد حالات معزولة لأنها غير موجودة في التفاصيل.",
            "least_problematic_fields_ar": "لا يمكن ترتيب الحقول دون أخطاء مرصودة في التفاصيل.",
            "recommendations_ar": [
                "إن كان التحليل بدون نموذج لغوي، جرّب التحليل بـ Gemini لاكتشاف تعارضات أدق.",
                "راجع عينة عشوائية من السجلات يدويًا للتحقق من جودة الإدخال.",
            ],
            "priority_fields_ar": [],
        }

    top = agg.get("most_repeated") or []
    top_bits = []
    for t in top[:8]:
        if not isinstance(t, dict):
            continue
        f, m, c = t.get("field"), t.get("message"), t.get("count")
        short_m = (m or "")[:140] + ("…" if len(str(m or "")) > 140 else "")
        top_bits.append(f"«{f}» ({c}×): {short_m}")
    most_txt = " ".join(top_bits) if top_bits else "لا بيانات."

    rare_n = int(agg.get("singleton_count", 0) or 0)
    rare_txt = (
        f"وُجد {rare_n} نوع خطأ ظهر مرة واحدة فقط (رسائل معزولة)، "
        "ما قد يشير إلى أخطاء إدخال فردية أو حالات استثنائية."
        if rare_n
        else "لا توجد أخطاء «مرة واحدة» ضمن التفاصيل المعروضة."
    )

    least_fields = agg.get("fields_by_errors_asc") or []
    least_bits = [f"«{x.get('field')}» ({x.get('error_mentions')} إشارة)" for x in least_fields[:8] if isinstance(x, dict)]
    least_txt = (
        "أقل الحقول تكرارًا للمشاكل (ضمن الحقول التي وُجد لها خطأ): " + "، ".join(least_bits)
        if least_bits
        else "لا يوجد ترتيب واضح."
    )

    prio = [str(x.get("field")) for x in (agg.get("fields_by_errors_desc") or [])[:6] if isinstance(x, dict)]

    return {
        "summary_ar": head + f" إجمالي ظهورات الأخطاء في الحقول: {agg.get('total_error_occurrences')}، وأنواع مميزة: {agg.get('unique_error_types')}.",
        "most_repeated_insights_ar": most_txt,
        "rare_and_isolated_ar": rare_txt,
        "least_problematic_fields_ar": least_txt,
        "recommendations_ar": [
            "ركّز تصحيح الدفعة على الأنماط الأعلى تكرارًا أولاً لتقليل العمل اليدوي.",
            "للرسائل المرة الواحدة: راجع السجل المحدد أو اعتبرها شذوذًا.",
            "وحّد تعليمات الإدخال للحقول الأكثر إشكالية في النموذج.",
        ],
        "priority_fields_ar": prio,
    }


async def _call_gemini_insights_prompt(prompt: str) -> dict[str, Any]:
    api_key = get_gemini_api_key()
    genai.configure(api_key=api_key)

    last_exc: Optional[Exception] = None
    for i, model_name in enumerate(_gemini_models()):
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                    max_output_tokens=8192,
                ),
            )
            response = await asyncio.to_thread(model.generate_content, prompt)
            content = (response.text or "{}").strip()
            return json.loads(content)
        except Exception as exc:
            last_exc = exc
            err = str(exc).lower()
            is_quota = "429" in err or "quota" in err or "rate" in err
            is_not_found = "404" in err or "not found" in err
            if is_not_found:
                continue
            if is_quota and i < len(_gemini_models()) - 1:
                await asyncio.sleep(1)
                continue
            break

    if last_exc:
        raise last_exc
    raise RuntimeError("Gemini insights: no model attempted")


async def generate_batch_insights_report(stats: dict[str, Any], results: list[dict]) -> dict[str, Any]:
    """
    تقرير نهاية التحليل: تكرار الأخطاء + تحليل عربي (Gemini أو احتياطي إحصائي).
    """
    agg = aggregate_dynamic_batch_errors(results)

    if not get_gemini_api_key():
        rep = _fallback_insights_report_ar(stats, agg)
        return {
            "ok": True,
            "provider": "fallback",
            "message": "لا يوجد مفتاح Gemini — عُرض تقرير إحصائي.",
            "report": rep,
            "aggregates": agg,
        }

    prompt = (
        "أنت محلل جودة بيانات استبيانات. أجب بـ JSON فقط دون أي نص خارج JSON.\n\n"
        "الإحصائيات على مستوى الصفوف:\n"
        f"{json.dumps(stats, ensure_ascii=False)}\n\n"
        "تجميع أخطاء الحقول (كل ظهور لـ (حقل + رسالة) يُعدّ مرة):\n"
        f"{json.dumps(agg, ensure_ascii=False, indent=2)}\n\n"
        "المطلوب — كائن JSON بالمفاتيح التالية بالعربية:\n"
        "summary_ar: ملخص تنفيذي في جملتين إلى أربع.\n"
        "most_repeated_insights_ar: فقرة تحليلية عن أشد الأخطاء تكراراً وماذا تعني لجودة النموذج.\n"
        "rare_and_isolated_ar: فقرة عن الأخطاء النادرة أو المرة الواحدة وما إن كانت مقلقة.\n"
        "least_problematic_fields_ar: فقرة عن الحقول الأقل تكراراً للمشاكل (من الحقول التي وُجد لها خطأ).\n"
        "recommendations_ar: مصفوفة نصوص، 5 إلى 10 توصيات عملية للمُدخل أو لمصمم الاستبيان.\n"
        "priority_fields_ar: مصفوفة أسماء حقول تستحق الأولوية في المراجعة.\n"
    )

    try:
        raw = await _call_gemini_insights_prompt(prompt)
        if not isinstance(raw, dict):
            raw = {}
        rep = _normalize_insight_report(raw)
        return {"ok": True, "provider": "gemini", "report": rep, "aggregates": agg}
    except Exception as exc:
        rep = _fallback_insights_report_ar(stats, agg)
        return {
            "ok": True,
            "provider": "fallback",
            "message": f"تعذّر توليد تقرير Gemini — عُرض تقرير إحصائي. ({str(exc)[:180]})",
            "report": rep,
            "aggregates": agg,
        }
