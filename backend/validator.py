import json
import os
import asyncio
import difflib
from typing import Any, Optional

from openai import AsyncOpenAI
import google.generativeai as genai

from prompts import SYSTEM_PROMPT, FEW_SHOT_EXAMPLES

from lfs_business_rules import apply_lfs_hybrid_rules, merge_hybrid_into_result
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


def set_gemini_api_key(api_key: Optional[str]) -> None:
    """تعيين مفتاح Gemini من الواجهة (للسيشن الحالي)."""
    global _gemini_api_key_override
    _gemini_api_key_override = (api_key or "").strip() or None


def get_gemini_api_key() -> str:
    """مفتاح Gemini: من التعيين في الواجهة أولاً، وإلا من .env."""
    if _gemini_api_key_override:
        return _gemini_api_key_override
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
    """التحقق من اتصال Gemini بعمل طلب بسيط."""
    api_key = get_gemini_api_key()
    if not api_key:
        return {"ok": False, "message": "مفتاح GEMINI_API_KEY غير مضبوط في .env"}
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name=_gemini_models()[0],
            generation_config=genai.GenerationConfig(temperature=0, max_output_tokens=10),
        )
        response = await asyncio.to_thread(model.generate_content, "قل: متصل")
        if response and response.text:
            return {"ok": True, "message": "متصل بـ Gemini بنجاح"}
        return {"ok": True, "message": "تم الاتصال"}
    except Exception as exc:
        err = str(exc).lower()
        if "api_key" in err or "invalid" in err or "401" in err:
            return {"ok": False, "message": "مفتاح API غير صالح أو منتهي"}
        if "429" in err or "quota" in err:
            return {"ok": False, "message": "تجاوز حد الاستخدام، جرّب لاحقاً"}
        if "network" in err or "connection" in err:
            return {"ok": False, "message": "فشل الاتصال بالشبكة"}
        return {"ok": False, "message": f"خطأ: {str(exc)[:120]}"}


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


async def validate_form(raw_data: dict) -> dict:
    clean = {k: v for k, v in raw_data.items() if v is not None and v != "" and v != 0 and k != "name"}

    if len(clean) < 2:
        return _empty_result()

    gemini_key = get_gemini_api_key()
    groq_key = os.getenv("GROQ_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    try:
        if gemini_key:
            return await _call_gemini(clean)

        if groq_key:
            return await _call_openai_compatible(
                clean,
                base_url="https://api.groq.com/openai/v1",
                api_key=groq_key,
                model="llama-3.3-70b-versatile",
            )

        if openai_key:
            return await _call_openai_compatible(
                clean,
                base_url="https://api.openai.com/v1",
                api_key=openai_key,
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            )

        return _mock_validate(clean)

    except Exception:
        return _mock_validate(clean)


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
        "• النصوص والتسميات: المسمى الوظيفي، المؤهل العلمي، الجنس، الحالة الاجتماعية، نوع السكن، جهة العمل، أي تسمية أو تصنيف — تحقق من التناسق بينها (مثلاً مؤهل «ابتدائي» مع مسمى «طبيب»، أو «أعزب» مع «عدد أبناء» كبير، أو عمر صغير مع منصب قيادي).\n"
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
                if apply_hybrid_rules:
                    sanitized = merge_hybrid_into_result(sanitized, apply_lfs_hybrid_rules(rec_full))
                results.append(sanitized)
            gemini_used = True
        except Exception:
            fallback_chunk = _dynamic_fallback(cols_use, chunk_llm)
            for fb in fallback_chunk["results"]:
                idx = int(fb.get("row_index", 0))
                full = next((cr for cr in chunk_full if int(cr["row_index"]) == idx), None)
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
    """تحقق فوري بالقواعد — للمعالجة الدفعية بدون LLM."""
    clean = {k: v for k, v in data.items() if v is not None and v != "" and v != 0 and k != "name"}
    if len(clean) < 2:
        return _empty_result()
    return _mock_validate(clean)


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
