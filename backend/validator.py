import json
import os
import asyncio
import difflib
from typing import Any

from openai import AsyncOpenAI
import google.generativeai as genai

from prompts import SYSTEM_PROMPT, FEW_SHOT_EXAMPLES


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


async def _call_gemini_prompt(prompt: str, api_key: str | None = None) -> dict:
    key = (api_key or os.getenv("GEMINI_API_KEY") or "").strip()
    if not key:
        raise ValueError("GEMINI_API_KEY not set")
    genai.configure(api_key=key)

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


async def check_gemini_connection(api_key: str | None = None) -> dict:
    """التحقق من اتصال Gemini بعمل طلب بسيط. إذا وُجد api_key يُستخدم وإلا من .env"""
    key = (api_key or os.getenv("GEMINI_API_KEY") or "").strip()
    if not key:
        return {"ok": False, "message": "مفتاح API غير مضبوط. أدخله في الحقل أعلاه أو في ملف .env"}
    try:
        genai.configure(api_key=key)
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

    gemini_key = os.getenv("GEMINI_API_KEY")
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


def _dynamic_fallback(columns: list[str], records: list[dict]) -> dict:
    results = []
    for rec in records:
        row_index = int(rec.get("row_index", 0))
        errors = []
        col_norms = {col: _norm_text(col) for col in columns}

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
                elif value < 0:
                    errors.append(
                        {"field": col, "message": f"القيمة ({value}) في '{col}' سالبة", "severity": "medium"}
                    )
                elif abs(value) > 1_000_000_000:
                    errors.append(
                        {"field": col, "message": f"القيمة في '{col}' كبيرة جداً وقد تكون خطأ", "severity": "high"}
                    )
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
                        except (TypeError, ValueError):
                            pass

        penalty = sum({"high": 35, "medium": 20, "low": 8}.get(e["severity"], 10) for e in errors)
        score = max(0, 100 - penalty)
        status = "valid" if not errors else ("warning" if score >= 50 else "error")
        results.append(
            {
                "row_index": row_index,
                "confidence_score": score,
                "status": status,
                "errors": errors,
                "suggestions": [] if not errors else ["راجع الحقول المميزة في هذا الصف"],
                "summary": "البيانات تبدو منطقية" if not errors else f"رُصد {len(errors)} تعارضات محتملة",
            }
        )

    return {"results": results, "stats": _compute_stats(results)}


def _build_dynamic_batch_prompt(columns: list[str], records_chunk: list[dict]) -> str:
    return (
        "أنت مدقق جودة بيانات خبير في اكتشاف التناقضات المنطقية والدلالية في أي نموذج استبيان.\n"
        "حلّل كل صف اعتماداً على العلاقة بين الحقول داخل نفس الصف فقط.\n\n"
        "المطلوب — تحليل كل شيء وليس الأرقام فقط:\n"
        "• الأرقام: عمر، رواتب، سنوات خبرة، أعداد — تحقق من المنطق والحدود.\n"
        "• النصوص والتسميات: المسمى الوظيفي، المؤهل العلمي، الجنس، الحالة الاجتماعية، نوع السكن، جهة العمل، أي تسمية أو تصنيف — تحقق من التناسق بينها (مثلاً مؤهل «ابتدائي» مع مسمى «طبيب»، أو «أعزب» مع «عدد أبناء» كبير، أو عمر صغير مع منصب قيادي).\n"
        "• أي حقل آخر: أسماء، فئات، تواريخ، نصوص حرة — راعِ التناسق مع باقي حقول نفس الصف.\n"
        "1) اكتشاف القيم غير المنطقية أو المتناقضة سياقياً في كل الحقول.\n"
        "2) إرجاع الأخطاء على مستوى الحقول مع ذكر اسم الحقل كما هو EXACT من قائمة الأعمدة.\n"
        "3) إرجاع درجة ثقة لكل صف من 0 إلى 100.\n\n"
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
        '          "message": "<سبب التعارض>",\n'
        '          "severity": "low|medium|high"\n'
        "        }\n"
        "      ],\n"
        '      "suggestions": ["..."],\n'
        '      "summary": "..."\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "تأكد من شمول كل row_index في الرد، حتى إن لم يوجد خطأ (errors = [])."
    )


async def validate_rows_dynamic(
    columns: list[str], records: list[dict], mode: str = "smart", gemini_api_key: str | None = None
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

    mode = (mode or "smart").lower().strip()
    if mode == "fast":
        out = _dynamic_fallback(columns, cleaned_records)
        out["provider"] = "local"
        return out

    gemini_key = (gemini_api_key or os.getenv("GEMINI_API_KEY") or "").strip()
    if not gemini_key:
        out = _dynamic_fallback(columns, cleaned_records)
        out["provider"] = "local"
        out["gemini_unavailable"] = True
        return out

    chunk_size = max(5, int(os.getenv("DYNAMIC_BATCH_SIZE", "20")))
    results = []
    gemini_used = False

    for i in range(0, len(cleaned_records), chunk_size):
        chunk = cleaned_records[i : i + chunk_size]
        try:
            prompt = _build_dynamic_batch_prompt(columns, chunk)
            raw = await _call_gemini_prompt(prompt, api_key=gemini_key)
            model_results = raw.get("results") if isinstance(raw, dict) else []
            model_results = model_results if isinstance(model_results, list) else []

            by_index = {}
            for item in model_results:
                if isinstance(item, dict) and "row_index" in item:
                    by_index[int(item["row_index"])] = item

            for rec in chunk:
                idx = rec["row_index"]
                item = by_index.get(idx, {})
                results.append(_sanitize_dynamic_item(item, idx, columns))
            gemini_used = True
        except Exception:
            fallback_chunk = _dynamic_fallback(columns, chunk)
            results.extend(fallback_chunk["results"])

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
