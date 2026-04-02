import os
from dotenv import load_dotenv
from fastapi import FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response

from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Literal

load_dotenv()

# لا تستورد validator هنا — يحمّل google-generativeai وgrpc وثقيل على الذاكرة؛
# تأجيل الاستيراد يقلّل احتمال 502 على /openapi.json و/docs مع خطة Render المجانية (512MB).


def _env_truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in ("1", "true", "yes", "on")


def _gemini_key_in_env() -> bool:
    return bool((os.getenv("GEMINI_API_KEY") or "").strip())


def _supabase_gemini_configured() -> bool:
    """يوجد مفتاح فعلي في Supabase (بعد الجلب المؤقت)."""
    try:
        from supabase_settings import fetch_gemini_api_key_sync, supabase_settings_enabled as _sse

        if not _sse():
            return False
        return bool(fetch_gemini_api_key_sync())
    except Exception:
        return False


def _client_can_post_gemini_key() -> bool:
    """عند تعطيله في الإنتاج لا يُقبل المفتاح من المتصفح — فقط من متغيرات البيئة."""
    return not _env_truthy("DISABLE_CLIENT_GEMINI_KEY")


def _cors_allow_origins() -> list[str]:
    """محلياً + أي نطاقات تضيفها في ALLOWED_ORIGINS (مفصولة بفاصلة) للواجهة المنشورة."""
    defaults = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]
    raw = (os.getenv("ALLOWED_ORIGINS") or os.getenv("CORS_ORIGINS") or "").strip()
    extra = [o.strip().rstrip("/") for o in raw.split(",") if o.strip()]
    seen: set[str] = set()
    out: list[str] = []
    for o in defaults + extra:
        if o not in seen:
            seen.add(o)
            out.append(o)
    return out


app = FastAPI(
    title="الحارس الدلالي API",
    description="نظام ذكي للتحقق من التناقضات المنطقية في استمارات الاستبيان",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_allow_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
async def root():
    """جذر الخدمة — روابط مباشرة (Render يفحص أحياناً HEAD /)."""
    return {
        "service": "الحارس الدلالي API",
        "health": "/api/health",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


@app.head("/", include_in_schema=False)
async def root_head():
    return Response(status_code=200)


class FormData(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    education: Optional[str] = None
    job_title: Optional[str] = None
    years_experience: Optional[int] = None
    monthly_salary: Optional[float] = None
    sector: Optional[str] = None
    marital_status: Optional[str] = None
    children_count: Optional[int] = None


class GeminiApiKeyPayload(BaseModel):
    api_key: str = ""


class GeminiStatusResponse(BaseModel):
    """رد التحقق من Gemini — يظهر في OpenAPI بدل schema نوع string."""

    ok: bool
    message: str
    cached: Optional[bool] = None


@app.get("/api/health")
async def health():
    from supabase_settings import supabase_settings_enabled as _sse
    from validator import get_gemini_api_key

    has_gemini = bool(get_gemini_api_key())
    has_groq = bool(os.getenv("GROQ_API_KEY"))
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    configured = has_gemini or has_groq or has_openai
    if has_gemini:
        provider = "gemini"
    elif has_groq:
        provider = "groq"
    elif has_openai:
        provider = "openai"
    else:
        provider = "none"
    return {
        "status": "ok",
        "llm_configured": configured,
        "provider": provider,
        "mode": "live" if configured else "demo",
        "gemini_from_env": _gemini_key_in_env(),
        "supabase_settings_enabled": _sse(),
        "gemini_from_supabase": _supabase_gemini_configured(),
        "client_can_set_gemini_key": _client_can_post_gemini_key(),
    }


@app.get("/api/gemini-status", response_model=GeminiStatusResponse)
async def gemini_status():
    """التحقق من اتصال Gemini بعمل طلب فعلي."""
    from validator import check_gemini_connection

    return await check_gemini_connection()


@app.get("/api/supabase-status")
def supabase_status_check():
    """اختبار الاتصال بـ Supabase وجدول app_settings (بدون كشف أسرار)."""
    from supabase_settings import test_supabase_connection

    return test_supabase_connection()


@app.post("/api/gemini-api-key")
async def set_gemini_key(payload: GeminiApiKeyPayload):
    """تعيين مفتاح Gemini من الواجهة (للسيشن الحالي) — يُعطّل في الإنتاج بـ DISABLE_CLIENT_GEMINI_KEY."""
    if not _client_can_post_gemini_key():
        return JSONResponse(
            status_code=403,
            content={
                "ok": False,
                "message": "إرسال المفتاح من المتصفح معطّل. استخدم Supabase أو GEMINI_API_KEY على الخادم.",
            },
        )
    from validator import set_gemini_api_key

    set_gemini_api_key(payload.api_key or "")
    return {"ok": True, "message": "تم حفظ المفتاح"}


@app.post("/api/validate")
async def validate(data: FormData):
    from validator import validate_form

    result = await validate_form(data.model_dump())
    return result


class BatchRecord(BaseModel):
    row_index: int
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    education: Optional[str] = None
    job_title: Optional[str] = None
    years_experience: Optional[int] = None
    monthly_salary: Optional[float] = None
    sector: Optional[str] = None
    marital_status: Optional[str] = None
    children_count: Optional[int] = None


@app.post("/api/validate-batch")
async def validate_batch(records: List[BatchRecord]):
    """
    تحقق دفعي بنفس حقول الاستمارة المبسّطة.
    عند ضبط مفتاح LLM (Gemini / Groq / OpenAI) يُستخدم نفس مسار `/api/validate` (ذكي).
    بدون مفتاح يُستخدم التحقق السريع المحلي (`validate_form_quick`) — مكافئ لوضع العرض التوضيحي.
    """
    from validator import get_gemini_api_key, validate_form, validate_form_quick

    use_llm = bool(get_gemini_api_key()) or bool(os.getenv("GROQ_API_KEY")) or bool(os.getenv("OPENAI_API_KEY"))
    results = []
    for record in records:
        data = record.model_dump()
        row_index = data.pop("row_index")
        if use_llm:
            result = await validate_form(data)
        else:
            result = validate_form_quick(data)
        result["row_index"] = row_index
        results.append(result)
    total = len(results)
    errors_count = sum(1 for r in results if r["status"] == "error")
    warnings_count = sum(1 for r in results if r["status"] == "warning")
    avg_confidence = round(sum(r["confidence_score"] for r in results) / total) if total else 0
    return {
        "results": results,
        "stats": {
            "total": total,
            "errors": errors_count,
            "warnings": warnings_count,
            "valid": total - errors_count - warnings_count,
            "avg_confidence": avg_confidence,
        },
    }


class DynamicBatchPayload(BaseModel):
    columns: List[str]
    records: List[Dict[str, Any]]
    mode: Literal["fast", "smart"] = "smart"
    column_labels: Optional[Dict[str, str]] = None
    embed_metadata: bool = True
    column_subset: bool = True
    max_columns: Optional[int] = None
    apply_hybrid_rules: bool = True


@app.post("/api/validate-batch-dynamic")
async def validate_batch_dynamic(payload: DynamicBatchPayload):
    from validator import validate_rows_dynamic

    return await validate_rows_dynamic(
        payload.columns,
        payload.records,
        payload.mode,
        column_labels=payload.column_labels,
        embed_metadata=payload.embed_metadata,
        column_subset=payload.column_subset,
        max_columns=payload.max_columns,
        apply_hybrid_rules=payload.apply_hybrid_rules,
    )


@app.post("/api/admin/refresh-supabase-cache")
async def refresh_supabase_cache(x_admin_secret: Optional[str] = Header(None, alias="X-Admin-Secret")):
    """
    يمسح التخزين المؤقت لمفتاح Gemini من Supabase ليُعاد الجلب فوراً بعد تعديل الجدول.
    يتطلب ضبط ADMIN_SECRET في بيئة الخادم وإرساله في الترويسة X-Admin-Secret.
    """
    secret = (os.getenv("ADMIN_SECRET") or "").strip()
    if not secret:
        return JSONResponse(
            status_code=503,
            content={"ok": False, "message": "ADMIN_SECRET غير مضبوط على الخادم"},
        )
    if (x_admin_secret or "").strip() != secret:
        return JSONResponse(
            status_code=403,
            content={"ok": False, "message": "غير مصرّح"},
        )
    from supabase_settings import invalidate_gemini_key_cache

    invalidate_gemini_key_cache()
    return {"ok": True, "message": "تم مسح ذاكرة التخزين المؤقت — سيُجلب المفتاح من Supabase في الطلب التالي"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
