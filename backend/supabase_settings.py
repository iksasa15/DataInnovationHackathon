"""
قراءة إعدادات التطبيق من Supabase (جدول app_settings) عبر REST.
يُستخدم لمفتاح النموذج اللغوي القابل للتعديل من Table Editor دون إعادة نشر الخادم.

المتغيرات:
  SUPABASE_URL
  SUPABASE_SERVICE_ROLE_KEY  (سري — لا تضعه في الواجهة)
  SUPABASE_GEMINI_SETTING_KEY  (اختياري، افتراضي: gemini_api_key)
  SUPABASE_SETTINGS_CACHE_SECONDS  (افتراضي: 60)
"""

from __future__ import annotations

import os
import time
from typing import Optional

import httpx

_cache_value: Optional[str] = None
_cache_time: float = 0.0


def supabase_settings_enabled() -> bool:
    url = (os.getenv("SUPABASE_URL") or "").strip()
    key = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or "").strip()
    return bool(url and key)


def _setting_key_name() -> str:
    return (os.getenv("SUPABASE_GEMINI_SETTING_KEY") or "gemini_api_key").strip() or "gemini_api_key"


def _cache_ttl() -> int:
    try:
        return max(5, int(os.getenv("SUPABASE_SETTINGS_CACHE_SECONDS", "60")))
    except ValueError:
        return 60


def fetch_gemini_api_key_sync(*, force_refresh: bool = False) -> str:
    """
    يجلب قيمة المفتاح من الصف حيث config_key = gemini_api_key (أو الاسم المخصص).
    يُخزَّن مؤقتاً لتقليل الطلبات.
    """
    global _cache_value, _cache_time

    if not supabase_settings_enabled():
        return ""

    now = time.time()
    if (
        not force_refresh
        and _cache_value is not None
        and (now - _cache_time) < _cache_ttl()
    ):
        return _cache_value

    base = os.getenv("SUPABASE_URL", "").rstrip("/")
    service = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    row_key = _setting_key_name()
    url = f"{base}/rest/v1/app_settings"
    params = {"config_key": f"eq.{row_key}", "select": "config_value"}
    headers = {
        "apikey": service,
        "Authorization": f"Bearer {service}",
    }

    new_val = ""
    try:
        with httpx.Client(timeout=12.0) as client:
            r = client.get(url, params=params, headers=headers)
            r.raise_for_status()
            rows = r.json()
            if isinstance(rows, list) and rows:
                new_val = str(rows[0].get("config_value") or "").strip()
    except Exception:
        if _cache_value is not None:
            return _cache_value
        new_val = ""

    _cache_value = new_val
    _cache_time = now
    return new_val


def invalidate_gemini_key_cache() -> None:
    global _cache_value, _cache_time
    _cache_value = None
    _cache_time = 0.0


def test_supabase_connection() -> dict:
    """
    اختبار الاتصال بـ Supabase REST وجدول app_settings (بدون إرجاع أسرار).
    يُرجع: ok, message, configured, table_ok, gemini_row_filled
    """
    global _cache_value, _cache_time

    empty = {
        "ok": False,
        "configured": False,
        "table_ok": False,
        "gemini_row_filled": False,
        "message": "",
    }
    if not supabase_settings_enabled():
        empty["message"] = (
            "Supabase غير مضبوط على الخادم. أضف SUPABASE_URL و SUPABASE_SERVICE_ROLE_KEY في بيئة الـ backend."
        )
        return empty

    base = os.getenv("SUPABASE_URL", "").rstrip("/")
    service = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    row_key = _setting_key_name()
    headers = {
        "apikey": service,
        "Authorization": f"Bearer {service}",
    }

    try:
        with httpx.Client(timeout=15.0) as client:
            r = client.get(
                f"{base}/rest/v1/app_settings",
                params={
                    "select": "config_key,config_value",
                    "config_key": f"eq.{row_key}",
                },
                headers=headers,
            )
            if r.status_code == 401:
                return {
                    "ok": False,
                    "configured": True,
                    "table_ok": False,
                    "gemini_row_filled": False,
                    "message": "رفض المصادقة (401). تحقق من مفتاح service_role في لوحة Supabase.",
                }
            if r.status_code == 404:
                return {
                    "ok": False,
                    "configured": True,
                    "table_ok": False,
                    "gemini_row_filled": False,
                    "message": "الجدول غير موجود. نفّذ ملف supabase/schema.sql من SQL Editor.",
                }
            r.raise_for_status()
            rows = r.json()
            if not isinstance(rows, list):
                return {
                    "ok": False,
                    "configured": True,
                    "table_ok": False,
                    "gemini_row_filled": False,
                    "message": "رد غير متوقع من Supabase.",
                }

            if len(rows) == 0:
                invalidate_gemini_key_cache()
                return {
                    "ok": True,
                    "configured": True,
                    "table_ok": True,
                    "gemini_row_filled": False,
                    "message": f"الاتصال ناجح. لا يوجد صف بـ config_key = «{row_key}» — أضف صفاً من Table Editor أو نفّذ schema.sql.",
                }

            val = str(rows[0].get("config_value") or "").strip()
            filled = bool(val)
            _cache_value = val
            _cache_time = time.time()

            if filled:
                return {
                    "ok": True,
                    "configured": True,
                    "table_ok": True,
                    "gemini_row_filled": True,
                    "message": "الاتصال بـ Supabase ناجح، وصف مفتاح النموذج اللغوي في الجدول غير فارغ.",
                }
            return {
                "ok": True,
                "configured": True,
                "table_ok": True,
                "gemini_row_filled": False,
                "message": "الاتصال ناجح. عمود config_value للصف gemini_api_key فارغ — أضف مفتاح النموذج اللغوي من Table Editor.",
            }
    except httpx.HTTPStatusError as exc:
        code = exc.response.status_code
        hint = (exc.response.text or "")[:120]
        return {
            "ok": False,
            "configured": True,
            "table_ok": False,
            "gemini_row_filled": False,
            "message": f"خطأ HTTP {code} من Supabase. {hint}" if hint else f"خطأ HTTP {code} من Supabase.",
        }
    except Exception as exc:
        return {
            "ok": False,
            "configured": True,
            "table_ok": False,
            "gemini_row_filled": False,
            "message": f"فشل الاتصال: {str(exc)[:160]}",
        }
