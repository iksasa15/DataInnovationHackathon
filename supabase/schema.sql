-- نفّذ هذا في Supabase: SQL Editor → New query → Run
-- جدول إعدادات بسيط: عدّل config_value من Table Editor في أي وقت

create table if not exists public.app_settings (
  config_key text primary key,
  config_value text not null default '',
  updated_at timestamptz not null default now()
);

-- صف مفتاح Gemini (المفتاح الفعلي تضعه أنت من واجهة Supabase)
insert into public.app_settings (config_key, config_value)
values ('gemini_api_key', '')
on conflict (config_key) do nothing;

comment on table public.app_settings is 'إعدادات التطبيق — يقرأها الخادم فقط عبر service role';

-- RLS: لا تسمح للمتصفح المجهول بالقراءة (الخادم يستخدم service role ويتجاوز RLS)
alter table public.app_settings enable row level security;

-- لا تضف سياسات للـ anon/authenticated إن أردت أن يبقى الجدول للخادم فقط
