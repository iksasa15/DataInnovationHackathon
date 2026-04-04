# الحارس الدلالي (عين) — مساعد ذكي للتحقق من التناقضات المنطقية والدلالية

نموذج أولي يلبي **مسار المعالجة الذكية للبيانات** في **هاكاثون الابتكار في البيانات** (الطريق إلى الرياض 2026)، وفق **دليل المتسابق — المسار الثاني**.  
اسم التحدي في الوثيقة الرسمية: **المصحح الذكي للأخطاء المنطقية (الحارس الدلالي)**. الواجهة العامة تُعرض للمستخدم تحت اسم **عين**.

| العنصر | الرابط |
|--------|--------|
| **المستودع (GitHub)** | [iksasa15/DataInnovationHackathon](https://github.com/iksasa15/DataInnovationHackathon) — استنساخ: `https://github.com/iksasa15/DataInnovationHackathon.git` |
| **الواجهة المنشورة (GitHub Pages)** | [https://iksasa15.github.io/DataInnovationHackathon/#/](https://iksasa15.github.io/DataInnovationHackathon/#/) |
| **الاستمارة الحية** | […/#/survey](https://iksasa15.github.io/DataInnovationHackathon/#/survey) |
| **تحليل Excel / CSV** | […/#/analysis](https://iksasa15.github.io/DataInnovationHackathon/#/analysis) |
| **اختبارات (API، Swagger، تشخيص، نموذج لغوي)** | […/#/tests](https://iksasa15.github.io/DataInnovationHackathon/#/tests) |
| **الـ API (مثال منشور)** | `https://datainnovationhackathon.onrender.com` — يُضبط عبر `DataHackathon/.env.production` (`VITE_API_URL`) وSecret في GitHub Actions إن لزم |
| **الفيديو التوضيحي (YouTube)** | [youtu.be/tZ4r2iM9ieQ](https://youtu.be/tZ4r2iM9ieQ) |

> **مهم لـ GitHub Pages:** المصدر يجب أن يكون مجلد **`docs`** وليس جذر الفرع، وإلا يظهر نص README بدل التطبيق.  
> **Settings → Pages → Branch: `main` → Folder: `/docs`**.  
> Workflow **`Deploy frontend to GitHub Pages (docs)`** يبني Vue من `DataHackathon` ويدفع `dist` إلى `docs/`.

> **روابط مباشرة:** على Pages يُستخدم **توجيه الهاش** (`#/survey` وليس `/survey` فقط) لأن التطبيق SPA.

---

## فهرس

1. [مطابقة دليل المتسابق](#match-guide)
2. [المنهجية](#methodology)
3. [المتطلبات التقنية](#requirements)
4. [استنساخ وتشغيل محلي](#local-setup)
5. [دليل المحكّم](#judges)
6. [النشر Deploy](#deploy)
7. [مفاتيح API للمحكمين](#api-keys)
8. [الفيديو التوضيحي](#video)
9. [هيكل المستودع](#structure)
10. [التواصل والترخيص](#contact)

---

<a id="match-guide"></a>

## مطابقة دليل المتسابق

| مطلوب الدليل | تنفيذ في المشروع |
|--------------|------------------|
| رفع بيانات اختبار (Excel) مماثلة للتدريب | صفحة **تحليل الملف** — رفع Excel/CSV وتحقق دفعة عبر `/api/validate-batch-dynamic` |
| استمارة حية (Live Form) | صفحة **الحارس الدلالي** — تحقق أثناء الإدخال (مع **debounce** قصير بعد التوقف عن الكتابة) |
| ليس Excel وحده | الواجهة تدعم **الاثنين معاً** |
| ربط LLM بمنظومة الجمع | FastAPI + برومبتات + نموذج لغوي (ومسارات بديلة) + طبقة قواعد hybrid |
| تسليم: README + نشر + فيديو | هذا الملف + جدول الروابط أعلاه + قسم [الفيديو](#video) |
| مستودع خاص وإضافة المحكمين | حسب الدليل: **Private** ودعوة المحكمين قبل التقييم. المستودع الحالي على GitHub: [DataInnovationHackathon](https://github.com/iksasa15/DataInnovationHackathon) — عدّل الظهور (عام/خاص) حسب تعليمات اللجنة. |

**معيار التقييم الجوهري (الدليل):** القدرة على اكتشاف التناقضات **في أثناء الإدخال**. في الاستمارة يظهر التحقق بعد ملء حقول كافية وتوقف الإدخال لحظات (لتقليل طلبات الـ API)، مع عرض **درجة ثقة** و**حالة** و**ملاحظات** فور وصول الرد.

---

<a id="methodology"></a>

## المنهجية (ربط الـ LLM بمنصة الاستبيان)

1. **واجهة جمع**: الواجهة (Vue 3 + Vite) ترسل بيانات الاستمارة أو صفوف Excel إلى **REST API** (FastAPI).
2. **تحليل ذكي**: الخادم يبني **برومبتًا** يتضمن تعليمات عربية، **Few-Shot** (أمثلة مبسّطة + أمثلة بأسماء حقول LFS عند التحقق الديناميكي)، وقاموس **معاني الأعمدة** (ميتاداتا) عند توفرها.
3. **مزوّد LLM**: يُفضّل **نموذج لغوي مباشر** لمسار Excel الديناميكي (مخرجات JSON). يمكن استخدام **Groq** أو **OpenAI** لمسار الاستمارة عند ضبط المتغيرات في `backend/.env`.
4. **طبقة مكمّلة (قواعد صريحة)**: يُحمَّل جدول **`LFS_Business_Rules.xlsx`** عبر `openpyxl`؛ القواعد المُنفَّذة برمجياً (مثل 2001، 2011–2017) تُرجِع `rule_id` و`message_en` من الملف. قائمة القواعد: `GET /api/lfs-business-rules` (اختياري: `LFS_BUSINESS_RULES_XLSX` لمسار الملف).
5. **تقليص الأعمدة**: للجداول العريضة يُختار حد أقصى من الأعمدة ذات الأولوية + الأعمدة ذات القيم في الصف (`LFS_MAX_COLUMNS`).
6. **استخدام بيانات التدريب**: **محاكاة واختبار** عبر الـ API والواجهة؛ لا يُفترض **تدريب نموذج** على بيانات الهيئة داخل هذا المستودع (متوافق مع منهجية الدليل).

---

<a id="requirements"></a>

## المتطلبات التقنية

| المكوّن | الإصدار / الملاحظات |
|---------|---------------------|
| Python | 3.11+ |
| Node.js | 20.19+ أو 22.12+ (حسب `DataHackathon/package.json`) |
| npm | يأتي مع Node |
| متصفح حديث | Chrome / Edge / Firefox |

### مكتبات رئيسية

- **الخادم:** FastAPI، Uvicorn، `google-generativeai`، `openai`، Pydantic، httpx، **openpyxl** (قراءة `LFS_Business_Rules.xlsx`)؛ pandas في `requirements-scripts.txt` (سكربتات تقييم/ميتاداتا — اختياري على Render).
- **الواجهة:** Vue 3، Vue Router، Pinia، Vite، SheetJS (`xlsx`)، iconv-lite، **Chart.js** + **vue-chartjs** (رسوم مقارنة في الصفحة الرئيسية).

---

<a id="local-setup"></a>

## استنساخ المستودع والتشغيل المحلي

### 1) استنساخ

```bash
git clone https://github.com/iksasa15/DataInnovationHackathon.git
cd DataInnovationHackathon
```

### 2) إعداد الخادم (Backend)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

عدّل `backend/.env` وأضف مفتاحاً واحداً على الأقل للوضع الذكي:

- `GEMINI_API_KEY` (مُفضّل لـ Excel الديناميكي)، أو  
- `GROQ_API_KEY` / `OPENAI_API_KEY` (مسارات بديلة).

اختياري: `PORT` (افتراضي 8000)، `LFS_MAX_COLUMNS`، `DYNAMIC_BATCH_SIZE`.

للسكربتات المحلية (تقييم LFS): `pip install -r requirements-scripts.txt`

### 3) إعداد الواجهة (Frontend)

```bash
cd ../DataHackathon
npm install
```

أنشئ `.env` أو انسخ من `.env.example` وعيّن:

```env
VITE_API_URL=http://127.0.0.1:8000
```

### 4) التشغيل

**من جذر المشروع (موصى به):**

```bash
chmod +x run.sh
./run.sh
```

**أو طرفيتان:**

```bash
# 1 — API
cd backend && source .venv/bin/activate
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

```bash
# 2 — الواجهة
cd DataHackathon && npm run dev
```

- الواجهة: http://localhost:5173  
- الـ API: http://127.0.0.1:8000  
- Swagger: http://127.0.0.1:8000/docs  

### فحص سريع

```bash
curl -s http://127.0.0.1:8000/api/health
```

`mode: live` عند وجود مفتاح LLM؛ `demo` عند غيابه (سلوك تقريبي).

---

<a id="judges"></a>

## دليل المحكّم

### أ) التجربة على النسخة المنشورة (مُفضّل إن كان الـ API يعمل)

1. افتح [الرئيسية](https://iksasa15.github.io/DataInnovationHackathon/#/).
2. **استمارة حية:** […/#/survey](https://iksasa15.github.io/DataInnovationHackathon/#/survey) — املأ الحقول وانتظر ظهور نتيجة التحقق بعد توقف الإدخال قليلاً.
3. **Excel / CSV:** […/#/analysis](https://iksasa15.github.io/DataInnovationHackathon/#/analysis) — اسحب الملف ثم نفّذ التحليل/التحقق للدفعة.
4. **اختبارات تقنية:** […/#/tests](https://iksasa15.github.io/DataInnovationHackathon/#/tests) — عنوان الـ API الحالي، Swagger، `openapi.json`، فحص شامل، اتصال النموذج اللغوي (إن وُجد).

إن فشلت الطلبات من المتصفّح، راجع **CORS**: على خادم الـ API يجب أن يتضمن `ALLOWED_ORIGINS` عنوان الواجهة، مثال:

`https://iksasa15.github.io`

(بدون شرطة مائلة أخيرة؛ بدون مسار المستودع — الأصل `https://iksasa15.github.io` كافٍ عادةً لطلبات المتصفح من الصفحة المنشورة.)

### ب) التشغيل المحلي (بديل)

1. اتبع [استنساخ وتشغيل محلي](#استنساخ-المستودع-والتشغيل-المحلي) وضَع `GEMINI_API_KEY` (أو بديل) في `backend/.env`.
2. الاستمارة: http://localhost:5173/survey  
3. التحليل الجماعي: http://localhost:5173/analysis  

### ج) ملفات بيانات مرجعية (جذر المستودع محلياً)

- `LFS_Training_Dataset 3.xlsx` — بنية قريبة من الاستمارة الميدانية.  
- `MetaData_LFS_Training_Dataset.xlsx` — وصف الحقول (يُغذّي `backend/data/lfs_column_labels.json` عند التحديث بالسكربت إن لزم).  
- `LFS_Business_Rules.xlsx` — جدول قواعد العمل (يُقرأ في الخادم؛ نفس الملف يغذّي رسائل القواعد في الـ API).

### د) سكربت تقييم اختياري (سطر أوامر)

```bash
cd backend && source .venv/bin/activate
pip install -r requirements-scripts.txt
python scripts/eval_lfs_notes.py
```

يقرأ `LFS_Training_Dataset 3.xlsx` من جذر المشروع للمقارنة التقريبية مع عمود الملاحظات.

---

<a id="deploy"></a>

## النشر (Deploy) — خطوات عملية

> الواجهة والـ API على **نطاقين**: عيّن **`VITE_API_URL`** عند بناء الواجهة و **`ALLOWED_ORIGINS`** على الخادم ليشمل أصل الواجهة المنشورة.

### أ) نشر الـ API (مثال Render)

1. [Render](https://render.com) → **Web Service** أو **Blueprint** ([`render.yaml`](render.yaml) يوجّه إلى `backend`).
2. **Root Directory:** `backend`  
3. **Build:** `pip install -r requirements.txt`  
4. **Start:** `uvicorn main:app --host 0.0.0.0 --port $PORT`  
5. **Python 3.11.x** — في Environment عيّن `PYTHON_VERSION=3.11.9` إن بُني بإصدار أحدث وفشل `pydantic-core`. تجنّب 3.14+ على الخطط الصغيرة.
6. **Environment:**
   - `ALLOWED_ORIGINS` — مثال: `https://iksasa15.github.io` (أو نطاق Netlify/Vercel إن استخدمته).
   - مفتاح: `GEMINI_API_KEY` و/أو Supabase (`SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY`) حسب [`supabase/schema.sql`](supabase/schema.sql).
   - مُستحسن: `DISABLE_CLIENT_GEMINI_KEY=true`

**Railway / Fly.io / Cloud Run:** نفس فكرة Uvicorn ومجلد `backend`.

### ب) الواجهة على GitHub Pages (هذا المستودع)

- الملف [`.github/workflows/deploy-github-pages.yml`](.github/workflows/deploy-github-pages.yml) يبني مع `VITE_BASE_PATH=/DataInnovationHackathon/` و`VITE_GH_PAGES=true`.
- **`DataHackathon/.env.production`** يحتوي `VITE_API_URL` لإنتاج الواجهة المنشورة.
- يمكن تجاوز القيمة عبر **GitHub Secret** باسم `VITE_API_URL` في الـ workflow.

### ج) الواجهة على Netlify / Vercel / Cloudflare (بديل)

في `DataHackathon` أنشئ `.env.production`:

```env
VITE_API_URL=https://your-api.example.com
```

ثم `npm ci && npm run build` وانشر مجلد `dist` (Base directory = `DataHackathon`). راجع [`DataHackathon/netlify.toml`](DataHackathon/netlify.toml) لـ SPA.

### د) تحقق بعد النشر

- `https://<عنوان-api>/api/health` يعيد JSON.  
- جرّب الاستمارة والرفع من الواجهة؛ خطأ CORS يعني تعديل `ALLOWED_ORIGINS` (مع `https://`).

---

<a id="api-keys"></a>

## مفاتيح API للمحكمين

- **الأفضل:** `GEMINI_API_KEY` (أو Supabase `app_settings`) في **بيئة الخادم** فقط — المحكّم لا يحتاج لصق مفتاح في الواجهة عند التفعيل الصحيح.
- **إنتاج أقوى:** `DISABLE_CLIENT_GEMINI_KEY=true` على الخادم.
- **بناء الواجهة:** `VITE_HIDE_GEMINI_KEY_INPUT=true` لإخفاء حقل المفتاح (انظر `DataHackathon/.env.example`).
- وفق الدليل: تزويد **رصيد كافٍ** للمفاتيح المدفوعة عبر قناة آمنة؛ **لا ترفع أسراراً إلى Git** (`backend/.env` في `.gitignore`).

### تحديث مفتاح النموذج اللغوي عبر Supabase (دون إعادة نشر الواجهة)

1. نفّذ [`supabase/schema.sql`](supabase/schema.sql) في SQL Editor.  
2. جدول `app_settings` → مفتاح `gemini_api_key` في `config_value`.  
3. على الخادم: `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` (لا تُعرض في الواجهة).  
4. كاش ~60 ثانية؛ أو `POST /api/admin/refresh-supabase-cache` مع `X-Admin-Secret` إن عُيّن `ADMIN_SECRET`.

التفاصيل موسّعة كانت في النسخة السابقة من README؛ المنطق لم يتغير.

---

<a id="video"></a>

## الفيديو التوضيحي

حسب الدليل: فيديو **حتى 3 دقائق** يتضمن:

- خطوات النشر/التشغيل (أو الإشارة إلى هذا README + الرابط المنشور).  
- عرضاً **حياً** لاكتشاف التناقضات من الاستمارة.  
- إن أمكن: لقطة سريعة لرفع Excel والنتائج.

**رابط الفيديو التوضيحي:**

[https://youtu.be/tZ4r2iM9ieQ](https://youtu.be/tZ4r2iM9ieQ)

---

<a id="structure"></a>

## هيكل المستودع (مختصر)

```
DataInnovationHackathon/
├── .github/workflows/       # نشر الواجهة إلى docs/ (GitHub Pages)
├── supabase/
│   └── schema.sql           # app_settings لمفتاح النموذج اللغوي
├── backend/                 # FastAPI — تحقق، نموذج لغوي، hybrid، ميتاداتا LFS
│   ├── main.py
│   ├── supabase_settings.py
│   ├── validator.py
│   ├── prompts.py
│   ├── lfs_metadata.py
│   ├── lfs_business_rules.py
│   ├── data/lfs_column_labels.json
│   └── scripts/
├── DataHackathon/           # Vue 3 — رئيسية، استمارة، تحليل، اختبارات
├── run.sh
├── run-backend.sh
├── render.yaml
└── README.md
```

---

<a id="contact"></a>

## جهة التواصل (استفسارات الهاكاثون)

حسب الدليل الرسمي: **I.Hackathon@stats.gov.sa**

---

## ترخيص

يخضع المشروع لسياسة الفريق والهيئة؛ راجع شروط المسابقة والمستودع الخاص.
