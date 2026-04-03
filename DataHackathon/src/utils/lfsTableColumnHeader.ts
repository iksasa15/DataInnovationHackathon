/**
 * عناوين أعمدة الجدول: تصنيف + اسم مختصر (حتى لو وُجد نص السؤال الكامل في الميتاداتا).
 * السؤال الكامل يُعرَض في خاصية title / التلميح.
 */

import { sanitizeLfsQuestionForDisplay } from './lfsSanitize'

/** تسميات مختصرة ثابتة لأكثر الحقول شيوعاً (تغلب على الاختصار الآلي) */
export const LFS_SHORT_LABEL_OVERRIDES: Record<string, string> = {
  f_m_id: 'معرّف الفرد',
  sample_id: 'معرّف العينة',
  member_delete_status: 'حذف الفرد',
  q_825: 'عدم الإجابة',
  gender: 'الجنس',
  nationality: 'الجنسية',
  age: 'العمر',
  family_relation: 'صلة القرابة',
  marage_status: 'الحالة الاجتماعية',
  wave: 'الموجة',
  q_301: 'أعلى مؤهل',
  q_302_e_txt: 'التخصص',
  q_302: 'رمز التخصص',
  q_303: 'سنة التخرج',
  q_303_val: 'السنة',
  q_304: 'تدريب بجهة عمل',
  q_305: 'برنامج تعليمي حالياً',
  q_306: 'الالتحاق بالتعليم',
  q_307: 'تغيّر المؤهل الحالي',
  q_308: 'مستوى البرنامج الحالي',
  q_309_e_txt: 'تخصص حالي',
  q_309: 'رمز التخصص الحالي',
  q_309_txt: 'أخرى',
  q_310: 'دوام الطالب',
  q_311: 'وقت للعمل أثناء الدراسة',
  q_312_m: 'الشهر',
  q_312_y: 'السنة',
  q_313: 'دورات خلال 4 أسابيع',
  q_314: 'دورات خارج النظام',
  q_401: 'وصف الوضع الحالي',
  q_501: 'عمل بأجر (الفترة)',
  q_502: 'نشاط تجاري خاص',
  q_503: 'مساعدة أسرة بلا أجر',
  q_504: 'توصيل (أوبر/كريم)',
  q_505: 'بيع/شراء عقارات…',
  q_506: 'متدرب بأجر',
  q_507: 'أعمال حرة',
  q_508: 'بيع من المنزل',
  q_509: 'بيع عبر تطبيقات',
  q_510: 'عمل في البناء',
  q_511: 'إمام/مؤذن بأجر',
  q_512: 'عمل في نادٍ رياضي',
  q_513: 'زراعة/صيد…',
  q_514: 'غرض العمل',
  q_515: 'العمل لأجر',
  q_516: 'امتلاك نشاط/رخصة',
  q_517: 'أكثر من نشاط',
  q_518: 'إلغاء السجل',
  q_519: 'تاريخ إغلاق النشاط',
  q_520: 'طبيعة النشاط',
  q_521: 'ساعات في النشاط',
  q_522: 'تأمينات اجتماعية',
  q_523: 'عمل للجهة',
  q_524: 'غياب مؤقت عن العمل',
  q_525: 'سبب التغيب',
  q_526: 'دخل أثناء التغيب',
  q_527: 'مهام أثناء التوقف',
  q_528: 'مدة التغيب',
  q_531: 'عدد الوظائف',
  q_532: 'صفة العمل',
  q_533: 'تغيير وظيفة',
  q_549: 'عمل عن بُعد',
  q_550: 'أغلب العمل عن بُعد',
  q_551_y: 'سنة بداية العمل الحالي',
  q_552_y: 'سنة العمل الخاص',
  q_553: 'وسيلة إيجاد العمل',
  q_557: 'سبب العمل المؤقت',
  q_557_txt: 'أخرى',
  q_560: 'وظيفة ثانية',
  q_561: 'الوظيفة الثانية',
  q_562: 'قطاع الوظيفة الثانية',
  q_562_txt: 'أخرى',
  q_563_e_txt: 'اسم المنشأة (ثانية)',
  q_564_e_txt: 'نشاط الشركة (ثانية)',
  q_564: 'رمز النشاط',
  q_564_txt: 'أخرى',
  q_565_e_txt: 'المهنة (ثانية)',
  q_566_e_txt: 'المهام (ثانية)',
  q_567: 'رمز المهنة',
  q_567_txt: 'أخرى',
  q_568_h: 'ساعات رسمية (ثانية)',
  q_569_h: 'ساعات فعلية (ثانية)',
  q_570: 'رغبة بساعات إضافية',
  q_571: 'إمكانية ساعات أكثر',
  q_572: 'سبب عدم ساعات أكثر',
  q_573_h: 'ساعات إضافية مرغوبة',
  q_574: 'أقل من 35 ساعة',
  q_574_txt: 'أخرى',
  q_601: 'راتب/أجر الشهر',
  q_602: 'الأجر الشهري (نطاق)',
  q_602_val: 'الأجر (ر.س)',
  q_603: 'نطاق الراتب',
  q_701: 'بحث عن عمل (4 أسابيع)',
  q_702: 'قبول عمل',
  q_703: 'بدء عمل خلال 3 أشهر',
  q_704: 'الرغبة بالعمل',
  q_705: 'سبب عدم البحث',
  q_705_txt: 'أخرى',
  q_706: 'سبب عدم الرغبة',
  q_763: 'رفض عروض',
  q_707: 'منصة التوظيف',
  q_710: 'فرص ملف التعريف',
  q_711: 'التقدم لفرصة',
  q_712: 'مقابلة عمل',
  q_716: 'اختبار/مقابلة',
  q_717: 'وكالة توظيف',
  q_718: 'طلب عبر وكالة',
  q_719: 'طلب مباشر للجهات',
  q_720: 'مساعدة أقارب',
  q_835: 'طلب على وظائف درستها',
  q_836: 'غير مهتم بالإعلانات',
  q_731: 'مواقع مهنية/اجتماعية',
  q_732: 'تقديم على منصة',
  q_733: 'مقابلة من إعلان',
  q_734: 'قرض لنشاط',
  q_735: 'رخصة نشاط',
  q_736: 'تحضير نشاط',
  q_765: 'انتظار نتيجة',
  q_737: 'وسائل أخرى للبحث',
  q_737_txt: 'تحديد',
  q_738: 'بحث عن عمل',
  q_739: 'بدء العمل الأسبوع الماضي',
  q_740: 'بدء خلال أسبوعين',
  q_741: 'سبب عدم البدء',
  q_742: 'مدة البحث',
  q_766: 'أسباب +12 شهر',
  q_766_txt: 'أخرى',
  q_743: 'دوام جزئي/كامل',
  q_744: 'وسائل البحث',
  q_745: 'قبول عرض خاص',
  q_746: 'حد أقصى للتنقل',
  q_747: 'أقل ساعات يومية',
  q_767: 'الانتقال لمدينة أخرى',
  q_768: 'العمل بمساحة مشتركة',
  q_748: 'لم يعمل سابقاً',
  q_749: 'عمل سابق +3 أشهر',
  q_750: 'عمل عائلي',
  q_751: 'منذ التوقف',
  q_752: 'سبب التوقف',
  q_753: 'قبل التوقف',
  q_754_e_txt: 'المنتج/النشاط الرئيسي',
  q_755: 'رمز النشاط',
  q_756: 'قطاع آخر عمل',
  q_757_e_job: 'المسمى الوظيفي',
  q_757_e_obj: 'المهام الرئيسية',
  q_757: 'رمز المهنة',
  q_577: 'قرارات النشاط العائلي',
  q_578: 'توظيف بأجر',
  q_579: 'أنواع الأجور',
  q_580: 'تأمينات صاحب العمل',
  q_534: 'النشاط المؤسسي',
  q_534_txt: 'قطاع آخر',
  q_535: 'اسم المنشأة',
  q_535_txt: 'اسم جهة العمل',
  q_536_e_ec: 'عنوان النشاط',
  q_536_e_s: 'السلع/الخدمات',
  q_536: 'رمز ISIC (النشاط)',
  q_536_txt: 'أخرى',
  q_537_e_job: 'المسمى الوظيفي',
  q_537_e_obj: 'المهام الوظيفية',
  q_537: 'رمز المهنة',
  q_581: 'شكل تسجيل العمل',
  q_582: 'تسجيل النشاط',
  q_583: 'مصدر الدخل',
  q_584: 'العملاء عبر وسيط',
  q_585: 'صفة في العمل التجاري',
  q_541: 'نوع الاتفاق',
  q_539: 'سجل/رخصة الجهة',
  q_540: 'نوع الحسابات',
  q_543: 'مكان العمل',
  q_544: 'عدد العاملين',
  q_546: '5 عاملين أو أكثر',
  q_547: 'إجازة سنوية',
  q_548: 'إجازة مرضية',
  d_ilostat: 'الحالة الوظيفية',
  d_ystartwk: 'سنة بداية العمل',
  d_hwusual: 'ساعات اعتيادية',
  d_hwactual: 'ساعات فعلية',
  cut_5_total: 'مجموع ساعات اعتيادية',
  act_1_total: 'مجموع ساعات فعلية',
  admin_name: 'المنطقة الإدارية',
  last_result: 'حالة المعاينة',
  الملاحظة: 'ملاحظة',
}

function shortOverrideForTag(tag: string): string | undefined {
  const k = tag.trim()
  const o = LFS_SHORT_LABEL_OVERRIDES[k] ?? LFS_SHORT_LABEL_OVERRIDES[k.toLowerCase()]
  if (o) return o
  const lower = k.toLowerCase()
  for (const [key, val] of Object.entries(LFS_SHORT_LABEL_OVERRIDES)) {
    if (key.toLowerCase() === lower) return val
  }
  return undefined
}

/** تصنيف موجز للعمود (سطر فوق الاسم المختصر في رأس الجدول) */
export function getLfsColumnCategory(tag: string): string | null {
  const t = tag.trim().toLowerCase()
  if (/^(f_m_id|sample_id|member_delete_status|wave|q_825)$/.test(t)) return 'التعريف والفرد'
  if (/^(gender|age|nationality|family_relation|marage_status)$/.test(t)) return 'الخصائص الديموغرافية'
  const mq = /^q_(\d+)/.exec(t)
  if (mq?.[1]) {
    const n = parseInt(mq[1], 10)
    if (n >= 301 && n <= 399) return 'التعليم والتدريب'
    if (n >= 401 && n <= 499) return 'الحالة الاقتصادية'
    if (n >= 501 && n <= 599) return 'العمل والنشاط المؤسسي'
    if (n >= 601 && n <= 699) return 'الأجر والعلاقة التعاقدية'
    if (n >= 701 && n <= 799) return 'البحث عن عمل'
    if (n >= 801 && n <= 899) return 'السكن والأسرة'
    if (n >= 901) return 'أخرى'
  }
  if (/^d_|^cut_|^act_/.test(t)) return 'مؤشرات مشتقة'
  if (/^(admin_name|last_result|الملاحظة)$/.test(t)) return 'إداري'
  return null
}

export function abbreviateLfsHeaderText(text: string, maxLen = 34): string {
  const t = text.replace(/\s+/g, ' ').trim()
  if (t.length <= maxLen) return t
  const q = t.indexOf('؟')
  if (q >= 14 && q <= maxLen + 8) return t.slice(0, q + 1)
  const cutAt = t.search(/[،—–]/)
  if (cutAt >= 12 && cutAt <= maxLen + 4) return t.slice(0, cutAt).trim() + '…'
  return t.slice(0, Math.max(12, maxLen - 1)).trim() + '…'
}

export interface LfsTableHeaderResolved {
  category: string | null
  shortLabel: string
  fullQuestion: string
  technicalId: string
}

export function resolveLfsTableColumnHeader(
  tag: string,
  meta: Record<string, string>,
): LfsTableHeaderResolved {
  const technicalId = tag.trim()
  let rawMeta: string | undefined = meta[technicalId]
  if (!rawMeta) {
    const lower = technicalId.toLowerCase()
    for (const k of Object.keys(meta)) {
      if (k.toLowerCase() === lower) {
        rawMeta = meta[k]
        break
      }
    }
  }
  const fullQuestion = rawMeta ? sanitizeLfsQuestionForDisplay(rawMeta) : ''
  const category = getLfsColumnCategory(technicalId)
  const ov = shortOverrideForTag(technicalId)
  let shortLabel: string
  if (ov) shortLabel = ov
  else if (fullQuestion) shortLabel = abbreviateLfsHeaderText(fullQuestion, 36)
  else shortLabel = technicalId

  return {
    category,
    shortLabel,
    fullQuestion: fullQuestion || technicalId,
    technicalId,
  }
}

export function formatLfsColumnHeaderTooltip(r: LfsTableHeaderResolved): string {
  const parts = [r.technicalId]
  if (r.fullQuestion && r.fullQuestion !== r.technicalId) parts.push(r.fullQuestion)
  if (r.category) parts.push(`التصنيف: ${r.category}`)
  return parts.join('\n\n')
}
