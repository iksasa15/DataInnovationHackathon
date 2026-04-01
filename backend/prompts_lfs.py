"""
أمثلة Few-Shot بأسماء حقول LFS الفعلية (مختصرة) لتقوية اتساق مخرجات النموذج مع بيانات الاختبار.
"""

# مثالان: تناقض عمر/تعليم، وتناقض قطاع/نشاط (مستوحى من بنية LFS_Training_Dataset)
FEW_SHOT_LFS_EXAMPLES: list[dict] = [
    {
        "input": {
            "row_index": 0,
            "age": 16,
            "family_relation_desc": "1-رئيس الأسرة",
            "q_301_desc": "13-درجة البكالوريوس الأكاديمي في 3-4 سنوات",
            "q_302_e_txt": "محاسبة",
        },
        "output": {
            "confidence_score": 12,
            "status": "error",
            "errors": [
                {
                    "field": "q_301_desc",
                    "message": "عمر 16 عاماً يتعارض مع حصول الفرد على بكالوريوس (عادة يتطلب إكمالاً بعد الثانوية بسنوات)",
                    "severity": "high",
                },
                {
                    "field": "family_relation_desc",
                    "message": "رئيس أسرة دون سن 18 مع مؤهل جامعي يستوجب التحقق من صحة تاريخ الميلاد أو المؤهل",
                    "severity": "high",
                },
            ],
            "suggestions": [
                "راجع حقل العمر أو تاريخ الميلاد مقابل أعلى مؤهل",
                "تحقق من صحة إدخال المستوى التعليمي (q_301 / q_301_desc)",
            ],
            "summary": "تعارض قوي بين العمر المنخفض والمؤهل الجامعي المعلن.",
        },
    },
    {
        "input": {
            "row_index": 1,
            "age": 35,
            "q_534_desc": "4-عمالة منزلية",
            "q_535_txt": "الشركة السعودية للكهرباء",
            "q_536_desc": "1595-توليد الطاقة الكهربائية",
        },
        "output": {
            "confidence_score": 38,
            "status": "error",
            "errors": [
                {
                    "field": "q_534_desc",
                    "message": "تصنيف القطاع كـ«عمالة منزلية» لا يتسق عادة مع جهة عمل صناعية كبيرة (كهرباء) ونشاط توليد كهرباء",
                    "severity": "high",
                },
                {
                    "field": "q_536_desc",
                    "message": "نشاط توليد الطاقة الكهربائية لا ينسجم مع قطاع العمالة المنزلية المذكور",
                    "severity": "high",
                },
            ],
            "suggestions": [
                "راجع q_534 / q_534_desc ليتوافق مع طبيعة جهة العمل في q_535_txt",
                "وازن النشاط الاقتصادي q_536_desc مع القطاع المؤسسي",
            ],
            "summary": "تعارض دلالي محتمل بين قطاع العمل المعلن والنشاط وجهة العمل.",
        },
    },
    {
        "input": {
            "row_index": 2,
            "age": 42,
            "q_301_desc": "13-درجة البكالوريوس الأكاديمي في 3-4 سنوات",
            "q_534_desc": "1-القطاع الحكومي",
            "q_536_desc": "8411-الأنشطة العامة للإدارة العامة",
        },
        "output": {
            "confidence_score": 91,
            "status": "valid",
            "errors": [],
            "suggestions": [],
            "summary": "البيانات متسقة نسبياً بين العمر والمؤهل وقطاع العمل والنشاط.",
        },
    },
]


def format_few_shot_lfs_block() -> str:
    import json

    parts = ["\n=== أمثلة تدريبية (حقول LFS) ===\n"]
    for ex in FEW_SHOT_LFS_EXAMPLES:
        parts.append(
            "\nمثال — مدخلات:\n"
            + json.dumps(ex["input"], ensure_ascii=False, indent=2)
            + "\nمثال — ردّ صحيح:\n"
            + json.dumps(ex["output"], ensure_ascii=False, indent=2)
            + "\n"
        )
    return "".join(parts)
