import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Literal

from validator import validate_form, validate_form_quick, validate_rows_dynamic

load_dotenv()

app = FastAPI(
    title="الحارس الدلالي API",
    description="نظام ذكي للتحقق من التناقضات المنطقية في استمارات الاستبيان",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.get("/api/health")
async def health():
    has_gemini = bool(os.getenv("GEMINI_API_KEY"))
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
    }


@app.post("/api/validate")
async def validate(data: FormData):
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
    results = []
    for record in records:
        data = record.model_dump()
        row_index = data.pop("row_index")
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


@app.post("/api/validate-batch-dynamic")
async def validate_batch_dynamic(payload: DynamicBatchPayload):
    return await validate_rows_dynamic(payload.columns, payload.records, payload.mode)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
