# الحارس الدلالي — مساعد ذكي للتحقق من التناقضات المنطقية والدلالية

**[افتح التطبيق — الصفحة الرئيسية (GitHub Pages)](https://iksasa15.github.io/DataInnovationHackathon/#/)**

> **إن ظهر نص README بدل الواجهة:** المستودع كان ينشر **جذر الفرع** (`/`) فيعرض `README.md`. عيّن المصدر إلى مجلد **`docs`** بعد أول نشر ناجح من Actions:
>
> **Settings → Pages → Build and deployment → Deploy from a branch → Branch: `main` → Folder: `/docs`** (وليس `/ (root)`).
>
> الـ workflow **`Deploy frontend to GitHub Pages (docs)`** يبني Vue ويدفع `dist` إلى **`docs/`** على `main`. بعد الدمج انتظر اكتمال Actions أو شغّل الـ workflow يدوياً.
>
> روابط مباشرة للصفحات: `…/DataInnovationHackathon/#/` (رئيسية)، `…/#/survey`، `…/#/analysis` — تجنّب `/analysis` بدون `#` على Pages.

نموذج أولي (POC) لمسار **المعالجة الذكية للبيانات** في هاكثون الابتكار في البيانات (الطريق إلى الرياض 2026).  
يربط واجهات **نماذج لغوية كبيرة (LLM)** بمنظومة جمع البيانات: **استمارة حية** و**رفع ملفات Excel/CSV**، مع مخرجات موحّدة تشمل **درجة ثقة** و**حالة** (valid / warning / error) و**أخطاء مرتبطة بالحقول** و**اقتراحات**.

---

## المنهجية (ربط الـ LLM بمنصة الاستبيان)

1. **واجهة جمع**: الواجهة الأمامية (Vue 3 + Vite) ترسل بيانات الاستمارة أو صفوف Excel إلى **REST API** (FastAPI).
2. **تحليل ذكي**: الخادم يبني **برومبتًا** يتضمن تعليمات عربية، **Few-Shot** (أمثلة مبسّطة + أمثلة بأسماء حقول LFS عند التحقق الديناميكي)، وقاموس **معاني الأعمدة** (ميتاداتا) عند توفرها.
3. **مزوّد LLM**: يُفضّل **Google Gemini** لمسار Excel الديناميكي (مخرجات JSON). يمكن استخدام **Groq** أو **OpenAI** لمسار الاستمارة المبسّطة عند ضبط المتغيرات في `.env`.
4. **طبقة مكمّلة (قواعد صريحة)**: قواعد مستوحاة من **LFS Business Rules** تُطبَّق كـ **hybrid** وتُدمج مع مخرجات النموذج لتقليل الأخطاء الواضحة (عمر/تعليم، تعارض قطاع/نشاط في حالات محددة).
5. **تقليص الأعمدة**: للجداول العريضة (مثل LFS) يُختار حد أقصى من الأعمدة ذات الأولوية + الأعمدة ذات القيم في الصف لتقليل حجم الطلب إلى النموذج (`LFS_MAX_COLUMNS`).
6. **الاستخدام المقصود للبيانات**: البيانات المزوّدة تُستخدم **للمحاكاة والاختبار** عبر الـ API والواجهة؛ لا يُفترض **تدريب نموذج** على بيانات الهيئة داخل هذا المستودع.

---

## المتطلبات التقنية

| المكوّن | الإصدار / الملاحظات |
|---------|---------------------|
| Python | 3.11+ |
| Node.js | 20.19+ أو 22.12+ (حسب `DataHackathon/package.json`) |
| npm | يأتي مع Node |
| متصفح حديث | Chrome / Edge / Firefox |

### مكتبات رئيسية

- **الخادم**: FastAPI، Uvicorn، `google-generativeai`، `openai` (للمتوافقين مع OpenAI API)، pydantic، httpx، pandas/openpyxl (سكربتات التقييم/الميتاداتا).
- **الواجهة**: Vue 3، Vue Router، Vite، SheetJS (`xlsx`).

---

## استنساخ المستودع والتشغيل المحلي

### 1) استنساخ

```bash
git clone <رابط-المستودع-الخاص>.git
cd DataInnovationHackathon
```

### 2) إعداد الخادم (Backend)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # على Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

عدّل الملف `backend/.env` وأضف مفتاحًا واحدًا على الأقل للوضع الذكي:

- `GEMINI_API_KEY` (مُفضّل لتحليل Excel الديناميكي)، أو  
- `GROQ_API_KEY` / `OPENAI_API_KEY` (مسارات بديلة حسب الكود).

متغيرات اختيارية: `PORT` (افتراضي 8000)، `LFS_MAX_COLUMNS`، `DYNAMIC_BATCH_SIZE`.

### 3) إعداد الواجهة (Frontend)

```bash
cd ../DataHackathon
npm install
```

### 4) التشغيل

**خيار أ — سكربت واحد (يُشغّل الـ API ثم الواجهة):** من جذر المشروع

```bash
chmod +x run.sh
./run.sh
```

**خيار ب — طرفيتان:**

```bash
# الطرفية 1 — API
cd backend && source .venv/bin/activate
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

```bash
# الطرفية 2 — الواجهة
cd DataHackathon && npm run dev
```

- **الواجهة:** http://localhost:5173  
- **الـ API:** http://127.0.0.1:8000  
- **وثائق تفاعلية (Swagger):** http://127.0.0.1:8000/docs  

### فحص سريع

```bash
curl -s http://127.0.0.1:8000/api/health
```

يُرجع `mode: live` عند ضبط مفتاح LLM، و`demo` عند غيابه (تحقق محلي تقريبي).

---

## كيف يجرّب المحكّم الحل

### أ) الاستمارة الحية (Live Form)

1. افتح http://localhost:5173  
2. انتقل إلى مسار **الاستمارة**: http://localhost:5173/survey  
3. املأ الحقول؛ يُنفَّذ التحقق تلقائيًا بعد توقف الإدخال قصيرًا (debounce) وتظهر **درجة الثقة** والملاحظات.

### ب) رفع Excel / CSV (اختبار جماعي)

1. افتح: http://localhost:5173/analysis (أو `/excel` — يعيد التوجيه إلى نفس الصفحة).  
2. اسحب ملف **Excel** أو **CSV** (مثل ملف بيانات التدريب المزوّد من الجهة).  
3. اضغط زر التحليل/التحقق لإرسال الصفوف إلى `/api/validate-batch-dynamic` وعرض النتائج لكل صف.

ملفات الاختبار المرجعية (عند وضعها في جذر المستودع محليًا):

- `LFS_Training_Dataset 3.xlsx` — بيانات تجريبية ببنية قريبة من الاستمارة الميدانية.  
- `MetaData_LFS_Training_Dataset.xlsx` — وصف الحقول (يُستورد تلقائيًا عبر `backend/data/lfs_column_labels.json` بعد التحديث بالسكربت إن لزم).  
- `LFS_Business_Rules.xlsx` — مرجع قواعد العمل.

### ج) سكربت تقييم اختياري (سطر أوامر)

```bash
backend/.venv/bin/python backend/scripts/eval_lfs_notes.py
```

يقرأ `LFS_Training_Dataset 3.xlsx` من جذر المشروع ويشغّل مسار التحقق السريع للمقارنة التقريبية مع عمود الملاحظات.

---

## النشر (Deploy) — خطوات عملية

> وفق دليل المتسابق: رابط **واجهة عامة** + تعليمات تشغيل. الـ API والواجهة غالباً على **نطاقين**؛ يجب ضبط **`ALLOWED_ORIGINS`** و **`VITE_API_URL`**.

### أ) نشر الـ API (Backend) — مثال Render

1. ادفع المشروع إلى GitHub وادخل [Render](https://render.com) → **New** → **Blueprint** أو **Web Service**.  
2. إن استخدمت Blueprint: الملف [`render.yaml`](render.yaml) يوجّه `rootDir` إلى `backend`.  
3. يدوياً (Web Service):  
   - **Root Directory:** `backend`  
   - **Build Command:** `pip install -r requirements.txt`  
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`  
   - **Python:** **3.11.x** (في لوحة Render أو المتغير `PYTHON_VERSION`) — تجنّب **3.14+** لأن `pydantic-core` قد يُبنى من المصدر (Rust) ويفشل (`Read-only file system` / maturin). الملف [`backend/runtime.txt`](backend/runtime.txt) يثبّت الإصدار عند النشر من مجلد `backend`.  
4. في **Environment** أضف (حسب ما تستخدم):
   - `ALLOWED_ORIGINS` = رابط الواجهة المنشورة فقط، مثال: `https://اسمك.netlify.app` (بدون شرطة أخيرة؛ يمكن عدة عناوين مفصولة بفاصلة إن لزم).  
   - مفتاح Gemini: إما `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` + جدول `app_settings`، أو `GEMINI_API_KEY` مباشرة.  
   - (مُستحسن للإنتاج) `DISABLE_CLIENT_GEMINI_KEY=true`  
5. بعد النشر انسخ **رابط الخدمة** (مثل `https://alharis-api.onrender.com`) — هذا هو **عنوان الـ API**.

**Railway / Fly.io / Google Cloud Run:** نفس الفكرة: تشغيل `uvicorn main:app --host 0.0.0.0 --port $PORT` (أو المنفذ الذي توفره المنصة) ومجلد العمل = `backend`.

---

### ب) نشر الواجهة (Frontend) — مثال Netlify أو Vercel

1. أنشئ ملف بيئة **قبل البناء** (لا ترفعه لـ Git إن كان فيه أسرار؛ هنا عنوان API فقط):  
   في مجلد `DataHackathon` أنشئ `.env.production`:

   ```env
   VITE_API_URL=https://رابط-الـ-api-من-الخطوة-أ.onrender.com
   ```

2. من جذر `DataHackathon`:

   ```bash
   npm ci
   npm run build
   ```

3. ارفع مجلد **`dist`** إلى Netlify / Cloudflare Pages / Vercel، أو اربط المستودع مع:
   - **Base directory:** `DataHackathon`  
   - **Build command:** `npm run build`  
   - **Publish directory:** `dist`  
4. في Netlify يمكن استخدام [`DataHackathon/netlify.toml`](DataHackathon/netlify.toml) لإعادة توجيه SPA.

5. بعد ظهور رابط الواجهة، ارجع إلى **متغيرات الـ API** على Render وأضف/حدّث `ALLOWED_ORIGINS` ليشمل **نفس رابط الواجهة** ثم أعد نشر الـ API (أو انتظر إعادة التشغيل).

---

### ج) تحقق سريع

- من المتصفح: `https://رابط-ال-api/api/health` يجب أن يعيد JSON.  
- افتح الواجهة وجرب الاستمارة أو رفع Excel؛ إن ظهر خطأ CORS راجع `ALLOWED_ORIGINS` (بما فيه `https://` وليس `http` إلا إن كان الموقع على HTTP).

**عنوان النشر (يُحدَّث من الفريق):**  
`https://YOUR-FRONTEND.example.com` ← الواجهة للمحكمين | `https://YOUR-API.example.com` ← الـ API

---

## مفاتيح API للمحكمين

- **الأفضل للنشر:** ضبط `GEMINI_API_KEY` في **متغيرات بيئة الخادم** (Railway / Render / إلخ). عندها تُخفى الواجهة تلقائياً حقل «مفتاح Gemini» ويُظهر تنبيهاً أن المفتاح يُدار من الاستضافة — **المستخدم النهائي لا يحتاج إدخال مفتاح**. لتغيير المفتاح لاحقاً: عدّل المتغير في لوحة الاستضافة وأعد تشغيل الخادم (أو انتظر إعادة التشغيل التلقائي).  
- **إنتاج أقوى:** فعّل `DISABLE_CLIENT_GEMINI_KEY=true` على الخادم لرفض أي محاولة إرسال مفتاح من المتصفح.  
- **واجهة الإنتاج:** يمكن تعيين `VITE_HIDE_GEMINI_KEY_INPUT=true` عند `npm run build` (انظر `DataHackathon/.env.example`) لإخفاء الحقل حتى في بيئة التطوير المبنية.  
- يُفضّل تزويد المحكمين **برصيد كافٍ** عبر القنوات الآمنة؛ **لا تُرفع المفاتيح إلى Git** (`backend/.env` في `.gitignore`).

### تغيير مفتاح Gemini من Supabase (بدون إعادة نشر)

1. أنشئ مشروعاً في [Supabase](https://supabase.com) ونفّذ SQL من الملف [`supabase/schema.sql`](supabase/schema.sql) (SQL Editor).
2. من **Table Editor** → `app_settings` → الصف `gemini_api_key` → ضع المفتاح في العمود `config_value` واحفظ.
3. في بيئة الخادم (استضافة الـ API) أضف:
   - `SUPABASE_URL` = رابط المشروع  
   - `SUPABASE_SERVICE_ROLE_KEY` = **مفتاح service_role** (من Project Settings → API) — **لا** تضعه في الواجهة أو Git.
4. أولوية المفتاح في الخادم: **جلسة الواجهة (إن وُجدت)** ← **Supabase** (إن وُجدت قيمة) ← **`GEMINI_API_KEY` في البيئة**.
5. القراءة من Supabase تُخزَّن مؤقتاً (~60 ثانية). بعد تغيير المفتاح في الجدول يمكنك:
   - الانتظار حتى انتهاء المدة، أو  
   - استدعاء: `POST /api/admin/refresh-supabase-cache` مع الترويسة `X-Admin-Secret: <ADMIN_SECRET>` بعد ضبط `ADMIN_SECRET` في بيئة الخادم.

عند تفعيل Supabase يُخفى حقل المفتاح في الواجهة تلقائياً.

---

## الفيديو التوضيحي

- **الرابط (يُضاف عند التسليم):**  
  `https://YOUR-VIDEO-LINK.example.com`  
- المدة المطلوبة في الدليل: **حتى 3 دقائق** (نشر، استمارة حية، رفع Excel).

---

## هيكل المستودع (مختصر)

```
DataInnovationHackathon/
├── supabase/
│   └── schema.sql           # جدول app_settings لمفتاح Gemini
├── backend/                 # FastAPI — التحقق، Gemini، قواعد hybrid، ميتاداتا
│   ├── main.py
│   ├── supabase_settings.py # قراءة المفتاح من Supabase
│   ├── validator.py
│   ├── prompts.py
│   ├── lfs_metadata.py
│   ├── lfs_business_rules.py
│   ├── data/lfs_column_labels.json
│   └── scripts/
├── DataHackathon/           # Vue 3 — استمارة + رفع Excel
├── run.sh                   # تشغيل API + واجهة معًا
├── run-backend.sh
└── README.md
```

---

## جهة التواصل (استفسارات الهكاثون)

حسب الدليل الرسمي: **I.Hackathon@stats.gov.sa**

---

## ترخيص

يخضع المشروع لسياسة الفريق والهيئة؛ راجع شروط المسابقة والمستودع الخاص.
