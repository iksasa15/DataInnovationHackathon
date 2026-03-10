import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from validator import validate_form

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


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
