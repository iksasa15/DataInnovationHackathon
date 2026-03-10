import json
import os
import asyncio
from openai import AsyncOpenAI
import google.generativeai as genai
from prompts import SYSTEM_PROMPT, FEW_SHOT_EXAMPLES


def _build_gemini_prompt(form_data: dict) -> str:
    """يبني prompt نصي كامل مع أمثلة Few-Shot لـ Gemini."""
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
        messages.append({
            "role": "user",
            "content": f"حلّل بيانات الاستمارة التالية:\n{json.dumps(example['input'], ensure_ascii=False, indent=2)}"
        })
        messages.append({
            "role": "assistant",
            "content": json.dumps(example["output"], ensure_ascii=False, indent=2)
        })
    messages.append({
        "role": "user",
        "content": f"حلّل بيانات الاستمارة التالية:\n{json.dumps(form_data, ensure_ascii=False, indent=2)}"
    })
    return messages


async def _call_gemini(form_data: dict) -> dict:
    api_key = os.getenv("GEMINI_API_KEY")
    # نجرّب النماذج بالترتيب: lite أولاً (حصة أعلى) ثم flash
    models_to_try = [
        os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite"),
        "gemini-2.0-flash",
        "gemini-flash-latest",
    ]

    genai.configure(api_key=api_key)
    prompt = _build_gemini_prompt(form_data)
    last_exc = None

    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )
            response = await asyncio.to_thread(model.generate_content, prompt)
            return json.loads(response.text)
        except Exception as exc:
            last_exc = exc
            # إذا لم يكن 429 نوقف المحاولات
            if "429" not in str(exc) and "quota" not in str(exc).lower():
                break

    raise last_exc


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

    except Exception as exc:
        err_str = str(exc)
        # عند تجاوز الحصة (429) نرجع للنموذج الاحتياطي
        if "429" in err_str or "quota" in err_str.lower() or "rate" in err_str.lower():
            result = _mock_validate(clean)
            result["summary"] = "⚠ تجاوز حصة API — يعمل بالوضع التجريبي. " + result["summary"]
            return result
        return {
            "confidence_score": 50,
            "status": "warning",
            "errors": [],
            "suggestions": ["تعذّر الاتصال بالنموذج اللغوي — تحقق من مفتاح API"],
            "summary": f"خطأ في الاتصال: {err_str[:150]}",
        }


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

    MEDICAL_JOBS = ["طبيب", "طبيبة", "دكتور", "دكتورة", "صيدلاني", "صيدلانية"]
    ENGINEER_JOBS = ["مهندس", "مهندسة"]
    EXECUTIVE_JOBS = ["مدير عام", "رئيس تنفيذي", "نائب رئيس"]
    LOW_EDU = ["ابتدائي", "متوسط", "إعدادي"]
    DIPLOMA_EDU = ["دبلوم", "ثانوي"]

    if age and years_exp:
        max_possible_exp = age - 15
        if years_exp > max_possible_exp:
            errors.append({
                "field": "years_experience",
                "message": (
                    f"سنوات الخبرة ({years_exp}) غير منطقية مع العمر ({age}) — "
                    f"الحد الأقصى المعقول هو {max(0, max_possible_exp)} سنة"
                ),
                "severity": "high",
            })

    if job_title:
        if any(j in job_title for j in MEDICAL_JOBS) and education in LOW_EDU + DIPLOMA_EDU:
            errors.append({
                "field": "education",
                "message": f"'{job_title}' يتطلب بكالوريوس على الأقل — المؤهل '{education}' لا يؤهل لممارسة المهنة الطبية",
                "severity": "high",
            })
        elif any(j in job_title for j in ENGINEER_JOBS) and education in LOW_EDU:
            errors.append({
                "field": "education",
                "message": f"'{job_title}' يتطلب بكالوريوس هندسة على الأقل — المؤهل الحالي غير كافٍ",
                "severity": "high",
            })
        elif any(j in job_title for j in EXECUTIVE_JOBS):
            if age and age < 30:
                errors.append({
                    "field": "job_title",
                    "message": f"منصب '{job_title}' نادراً ما يُشغله شخص دون الثلاثين — تحقق من صحة المسمى",
                    "severity": "medium",
                })
            if years_exp is not None and years_exp < 8:
                errors.append({
                    "field": "years_experience",
                    "message": f"منصب '{job_title}' عادةً يستلزم خبرة 10 سنوات فأكثر",
                    "severity": "medium",
                })

    if children > 0 and marital == "أعزب":
        errors.append({
            "field": "children_count",
            "message": f"وجود {children} أبناء مع الحالة الاجتماعية 'أعزب' يستوجب التحقق من المستجيب",
            "severity": "medium",
        })

    if salary and salary > 0:
        if job_title and any(j in job_title for j in ["موظف", "موظفة", "سائق", "عامل"]) and salary > 50000:
            errors.append({
                "field": "monthly_salary",
                "message": f"الراتب ({salary:,.0f} ر.س) مرتفع جداً بالنسبة لمسمى '{job_title}'",
                "severity": "low",
            })

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

    summary = (
        "البيانات متسقة ومنطقية — لا توجد تعارضات مرصودة."
        if not errors
        else f"رُصد {len(errors)} {'تعارض' if len(errors) == 1 else 'تعارضات'} تستوجب المراجعة."
    )

    return {
        "confidence_score": confidence,
        "status": status,
        "errors": errors,
        "suggestions": suggestions,
        "summary": summary,
    }
