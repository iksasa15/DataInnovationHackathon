/** تقرير تصدير HTML بنفس ألوان وهوية المنصة (ليس نصاً عادياً) */

export interface AnalysisExportIssueSection {
  rowNum: number
  statusAr: string
  summary: string
  problems: string[]
}

export interface AnalysisExportModification {
  row_index: number
  col: string
  oldVal: string
  newVal: string
}

export interface BatchStatsLike {
  total: number
  errors: number
  warnings: number
  valid: number
  avg_confidence: number
}

/** محتوى «تقرير نهاية التحليل» كاملاً كما في الواجهة */
export interface AnalysisExportInsightsFull {
  provider: 'gemini' | 'fallback'
  message?: string
  summaryAr: string
  mostRepeatedInsightsAr: string
  rareAndIsolatedAr: string
  /** إن وُجد في استجابة الخادم */
  leastProblematicFieldsAr?: string
  priorityFieldLabels: string[]
  total_error_occurrences?: number
  unique_error_types?: number
  singleton_count?: number
  mostRepeatedRows: { fieldLabel: string; count: number; message: string }[]
  topFieldsRows: { fieldLabel: string; error_mentions: number }[]
}

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

/**
 * يبنى مستند HTML كامل (UTF-8، RTL) جاهز للحفظ والفتح في المتصفح.
 */
function renderInsightsFullSection(ins: AnalysisExportInsightsFull): string {
  const prov =
    ins.provider === 'gemini'
      ? '<span class="prov-badge prov-gemini">نموذج لغوي</span>'
      : '<span class="prov-badge prov-fb">تحليل إحصائي</span>'
  const msg = ins.message?.trim()
    ? `<p class="ins-note"><strong>ملاحظة:</strong> ${escapeHtml(ins.message)}</p>`
    : ''
  const metrics =
    ins.total_error_occurrences != null ||
    ins.unique_error_types != null ||
    ins.singleton_count != null
      ? `<div class="agg-mini">
  ${ins.total_error_occurrences != null ? `<span>إجمالي إشارات الخطأ: <strong>${escapeHtml(String(ins.total_error_occurrences))}</strong></span>` : ''}
  ${ins.unique_error_types != null ? `<span>أنواع مميزة: <strong>${escapeHtml(String(ins.unique_error_types))}</strong></span>` : ''}
  ${ins.singleton_count != null ? `<span>أخطاء «مرة واحدة»: <strong>${escapeHtml(String(ins.singleton_count))}</strong></span>` : ''}
</div>`
      : ''
  const mrTable =
    ins.mostRepeatedRows.length > 0
      ? `<table class="ins-table">
  <thead><tr><th>الحقل</th><th>التكرار</th><th>الرسالة</th></tr></thead>
  <tbody>
    ${ins.mostRepeatedRows
      .map(
        (r) =>
          `<tr><td>${escapeHtml(r.fieldLabel)}</td><td>${escapeHtml(String(r.count))}</td><td>${escapeHtml(r.message)}</td></tr>`,
      )
      .join('')}
  </tbody>
</table>`
      : ''
  const topFields =
    ins.topFieldsRows.length > 0
      ? `<table class="ins-table">
  <thead><tr><th>الحقل</th><th>عدد إشارات الخطأ</th></tr></thead>
  <tbody>
    ${ins.topFieldsRows
      .map((r) => `<tr><td>${escapeHtml(r.fieldLabel)}</td><td>${escapeHtml(String(r.error_mentions))}</td></tr>`)
      .join('')}
  </tbody>
</table>`
      : ''
  const prio =
    ins.priorityFieldLabels.length > 0
      ? `<div class="prio-wrap">${ins.priorityFieldLabels.map((p) => `<span class="prio-chip">${escapeHtml(p)}</span>`).join('')}</div>`
      : ''

  const interpretRepeated =
    ins.mostRepeatedInsightsAr?.trim() !== ''
      ? `<h3>تفسير أعلى التكرار</h3>
    <div class="ins-text">${escapeHtml(ins.mostRepeatedInsightsAr)}</div>`
      : ''
  const interpretRare =
    ins.rareAndIsolatedAr?.trim() !== ''
      ? `<h3>تفسير الأخطاء النادرة أو المعزولة</h3>
    <div class="ins-text">${escapeHtml(ins.rareAndIsolatedAr)}</div>`
      : ''

  return `
  <section class="card card-insights">
    <h2>تقرير نهاية التحليل (كامل)</h2>
    <p class="prov-line">${prov}</p>
    ${msg}
    ${metrics}
    <h3>الملخص التنفيذي</h3>
    <div class="ins-text">${escapeHtml(ins.summaryAr)}</div>
    <h3>تفاصيل أعلى التكرار (حقل + رسالة)</h3>
    ${mrTable || '<p class="muted">لا توجد بيانات.</p>'}
    <h3>أكثر الحقول إشارات للخطأ</h3>
    ${topFields || '<p class="muted">لا توجد بيانات.</p>'}
    ${interpretRepeated}
    ${interpretRare}
    ${
      ins.leastProblematicFieldsAr?.trim()
        ? `<h3>حقول بأقل تكرار للمشاكل</h3><div class="ins-text">${escapeHtml(ins.leastProblematicFieldsAr)}</div>`
        : ''
    }
    <h3>أولوية المراجعة</h3>
    ${prio || '<p class="muted">—</p>'}
  </section>`
}

function renderInsightsMissingSection(): string {
  return `
  <section class="card card-insights card-insights--empty">
    <h2>تقرير نهاية التحليل (كامل)</h2>
    <p class="muted">لم يُتَاح تقرير نهاية التحليل الموسّع. يظهر بعد اكتمال التحليل ونجاح جلب التقرير من الخادم (نفس محتوى لوحة التقرير في المنصة).</p>
  </section>`
}

export function buildAnalysisExportReportHtml(opts: {
  /** عنوان المستند ونافذة المتصفح */
  documentTitle: string
  /** اسم الملف الأصلي (للعرض فقط) */
  sourceFileLabel: string
  stats: BatchStatsLike | null
  /** تقرير نهاية التحليل الكامل؛ إن وُجد يُدرَج كاملاً */
  insightsFull: AnalysisExportInsightsFull | null
  issueSections: AnalysisExportIssueSection[]
  noIssuesMessage: string
  modifications: AnalysisExportModification[]
}): string {
  const { documentTitle, sourceFileLabel, stats, insightsFull, issueSections, noIssuesMessage, modifications } = opts

  const statsBlock = stats
    ? `
  <section class="card">
    <h2>ملخص التحليل</h2>
    <div class="stats-grid">
      <div class="stat"><span class="stat-num">${escapeHtml(String(stats.total))}</span><span class="stat-lbl">إجمالي السجلات</span></div>
      <div class="stat stat-bad"><span class="stat-num">${escapeHtml(String(stats.errors))}</span><span class="stat-lbl">بها أخطاء</span></div>
      <div class="stat stat-warn"><span class="stat-num">${escapeHtml(String(stats.warnings))}</span><span class="stat-lbl">تحذيرات</span></div>
      <div class="stat stat-ok"><span class="stat-num">${escapeHtml(String(stats.valid))}</span><span class="stat-lbl">سليمة</span></div>
      <div class="stat stat-conf"><span class="stat-num">${escapeHtml(String(stats.avg_confidence))}%</span><span class="stat-lbl">متوسط الثقة</span></div>
    </div>
  </section>`
    : ''

  const issuesHtml =
    issueSections.length > 0
      ? issueSections
          .map(
            (sec) => `
  <article class="issue-block">
    <header class="issue-h"><span class="issue-row">صف ${escapeHtml(String(sec.rowNum))}</span><span class="issue-badge">${escapeHtml(sec.statusAr)}</span></header>
    <p class="issue-sum">${escapeHtml(sec.summary)}</p>
    <ul class="issue-list">
      ${sec.problems.map((p) => `<li>${escapeHtml(p)}</li>`).join('')}
    </ul>
  </article>`,
          )
          .join('')
      : `<p class="muted">${escapeHtml(noIssuesMessage)}</p>`

  const modsRows =
    modifications.length > 0
      ? modifications
          .map(
            (m) =>
              `<tr><td>${escapeHtml(String(m.row_index + 1))}</td><td dir="auto">${escapeHtml(m.col)}</td><td dir="auto">${escapeHtml(m.oldVal)}</td><td dir="auto">${escapeHtml(m.newVal)}</td></tr>`,
          )
          .join('')
      : `<tr><td colspan="4" class="muted">لم يتم تعديل أي خلية.</td></tr>`

  const insightsSection = insightsFull ? renderInsightsFullSection(insightsFull) : renderInsightsMissingSection()

  return `<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>${escapeHtml(documentTitle)}</title>
  <style>
    :root {
      --ga-primary: #4137a8;
      --ga-primary-mid: #5247b8;
      --ga-primary-dark: #322a82;
      --ga-primary-soft: #ebe8f7;
      --ga-surface: #f4f6f9;
      --text: #1e293b;
      --muted: #64748b;
      --bad: #b91c1c;
      --bad-bg: #fef2f2;
      --warn: #b45309;
      --warn-bg: #fffbeb;
      --ok: #15803d;
      --ok-bg: #f0fdf4;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: 'Frutiger LT Arabic', 'Segoe UI', Tahoma, system-ui, sans-serif;
      font-size: 15px;
      line-height: 1.65;
      color: var(--text);
      background: var(--ga-surface);
    }
    .brand {
      background: linear-gradient(135deg, #3d3690 0%, var(--ga-primary) 45%, #322a78 100%);
      color: #fff;
      padding: 1.25rem 1.5rem 1.35rem;
      box-shadow: 0 2px 12px rgba(50, 42, 130, 0.25);
    }
    .brand h1 {
      margin: 0 0 0.35rem;
      font-size: 1.35rem;
      font-weight: 800;
      letter-spacing: 0.02em;
    }
    .brand .sub {
      margin: 0;
      font-size: 0.88rem;
      opacity: 0.92;
    }
    .brand .file {
      margin-top: 0.65rem;
      font-size: 0.8rem;
      opacity: 0.85;
      word-break: break-word;
    }
    main { max-width: 52rem; margin: 0 auto; padding: 1.25rem 1rem 2rem; }
    h2 {
      margin: 0 0 0.65rem;
      font-size: 1.05rem;
      font-weight: 800;
      color: var(--ga-primary-dark);
      border-right: 4px solid var(--ga-primary);
      padding-right: 0.5rem;
    }
    .card {
      background: #fff;
      border: 1px solid #e2e8f0;
      border-radius: 0.65rem;
      padding: 1rem 1.1rem;
      margin-bottom: 1rem;
      box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
    }
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(8.5rem, 1fr));
      gap: 0.65rem;
    }
    .stat {
      text-align: center;
      padding: 0.55rem 0.45rem;
      border-radius: 0.45rem;
      background: var(--ga-primary-soft);
      border: 1px solid rgba(65, 55, 168, 0.15);
    }
    .stat-num { display: block; font-size: 1.25rem; font-weight: 800; color: var(--ga-primary-dark); }
    .stat-lbl { font-size: 0.72rem; color: var(--muted); }
    .stat-bad { background: var(--bad-bg); border-color: rgba(185, 28, 28, 0.2); }
    .stat-bad .stat-num { color: var(--bad); }
    .stat-warn { background: var(--warn-bg); border-color: rgba(245, 158, 11, 0.35); }
    .stat-warn .stat-num { color: var(--warn); }
    .stat-ok { background: var(--ok-bg); border-color: rgba(21, 128, 61, 0.2); }
    .stat-ok .stat-num { color: var(--ok); }
    .stat-conf .stat-num { color: var(--ga-primary-dark); }
    .issue-block {
      background: #fff;
      border: 1px solid #e2e8f0;
      border-radius: 0.55rem;
      padding: 0.85rem 1rem;
      margin-bottom: 0.65rem;
      border-right: 4px solid var(--ga-primary);
    }
    .issue-h { display: flex; flex-wrap: wrap; align-items: center; gap: 0.5rem; margin-bottom: 0.45rem; }
    .issue-row { font-weight: 800; color: var(--ga-primary-dark); }
    .issue-badge {
      font-size: 0.72rem;
      font-weight: 700;
      padding: 0.15rem 0.45rem;
      border-radius: 0.3rem;
      background: rgba(65, 55, 168, 0.12);
      color: var(--ga-primary-dark);
    }
    .issue-sum { margin: 0 0 0.45rem; font-size: 0.92rem; }
    .issue-list { margin: 0; padding-right: 1.15rem; font-size: 0.88rem; }
    .issue-list li { margin-bottom: 0.25rem; }
    table { width: 100%; border-collapse: collapse; font-size: 0.86rem; margin-top: 0.35rem; }
    th, td { border: 1px solid #e2e8f0; padding: 0.45rem 0.55rem; text-align: right; vertical-align: top; }
    th { background: var(--ga-surface); font-weight: 700; color: var(--ga-primary-dark); }
    .muted { color: var(--muted); font-size: 0.9rem; }
    h3 {
      margin: 1rem 0 0.4rem;
      font-size: 0.95rem;
      font-weight: 800;
      color: var(--ga-primary-dark);
    }
    .card-insights h2 { margin-bottom: 0.5rem; }
    .prov-line { margin: 0 0 0.65rem; }
    .prov-badge {
      display: inline-block;
      font-size: 0.72rem;
      font-weight: 700;
      padding: 0.2rem 0.55rem;
      border-radius: 999px;
    }
    .prov-gemini { background: rgba(16, 185, 129, 0.2); color: #047857; }
    .prov-fb { background: rgba(100, 116, 139, 0.18); color: #334155; }
    .ins-note { font-size: 0.86rem; margin: 0 0 0.75rem; }
    .agg-mini {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem 1rem;
      margin: 0 0 0.85rem;
      font-size: 0.82rem;
      padding: 0.5rem 0.65rem;
      background: var(--ga-surface);
      border-radius: 0.45rem;
      border: 1px solid #e2e8f0;
    }
    .ins-text {
      white-space: pre-wrap;
      word-break: break-word;
      font-size: 0.9rem;
      line-height: 1.7;
      margin: 0 0 0.85rem;
      padding: 0.65rem 0.75rem;
      background: #fafbfc;
      border-radius: 0.45rem;
      border: 1px solid #eef2f7;
    }
    .ins-table { margin-top: 0.35rem; margin-bottom: 0.75rem; }
    .prio-wrap { display: flex; flex-wrap: wrap; gap: 0.35rem; margin: 0.35rem 0 0.75rem; }
    .prio-chip {
      font-size: 0.76rem;
      padding: 0.2rem 0.5rem;
      border-radius: 999px;
      background: var(--ga-primary-soft);
      border: 1px solid rgba(65, 55, 168, 0.22);
      color: var(--ga-primary-dark);
    }
    footer {
      text-align: center;
      padding: 1rem;
      font-size: 0.78rem;
      color: var(--muted);
      border-top: 1px solid #e2e8f0;
      background: #fff;
    }
  </style>
</head>
<body>
  <header class="brand">
    <h1>منصة عين</h1>
    <p class="sub">تقرير التحليل والتعديلات — نسخة كاملة</p>
    <p class="file">الملف: ${escapeHtml(sourceFileLabel)}</p>
  </header>
  <main>
    ${statsBlock}
    ${insightsSection}
    <section class="card">
      <h2>الأخطاء والتحذيرات المرصودة (حسب الصف)</h2>
      ${issuesHtml}
    </section>
    <section class="card">
      <h2>التعديلات التي أجراها المستخدم</h2>
      <table>
        <thead>
          <tr>
            <th>الصف</th>
            <th>العمود</th>
            <th>قبل</th>
            <th>بعد</th>
          </tr>
        </thead>
        <tbody>${modsRows}</tbody>
      </table>
    </section>
  </main>
  <footer>هوية بصرية: الهيئة العامة للإحصاء — ألوان الأساسي #4137A8 · منصة عين</footer>
</body>
</html>`
}
