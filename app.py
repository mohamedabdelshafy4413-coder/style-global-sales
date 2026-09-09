from __future__ import annotations

import os
from io import BytesIO

import pandas as pd
import streamlit as st

from core.campaign_generator import generate_email
from core.golden500_engine import build_golden500
from core.upload_engine import analyze_uploaded_file

st.set_page_config(
    page_title="STYLE Golden 500 Buyer OS",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

COUNTRIES = [
    "Saudi Arabia",
    "United Arab Emirates",
    "Morocco",
    "United Kingdom",
    "United States",
    "France",
    "Germany",
    "Italy",
    "Spain",
    "Canada",
]

BUYER_TYPES = [
    "Importer",
    "Distributor",
    "Wholesaler",
    "Fabricator",
    "Contractor",
    "Developer",
    "Architectural Supplier",
    "Hotel / Hospitality Supplier",
    "Stone Showroom",
    "Project Procurement",
]

MATERIALS = [
    "Galala Light",
    "Sunny Light",
    "Meli Brown",
    "Meli Grey",
    "Zafarana Flower",
]


def secret(name: str) -> str:
    try:
        value = st.secrets.get(name, "")
        if value:
            return value
    except Exception:
        pass
    return os.getenv(name, "")


def excel_bytes(df: pd.DataFrame, sheet: str = "Golden 500") -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet[:31])
    return output.getvalue()


def read_upload(uploaded_file) -> pd.DataFrame:
    if uploaded_file.name.lower().endswith(".csv"):
        return pd.read_csv(uploaded_file)
    return pd.read_excel(uploaded_file)


def campaign_export(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in df.iterrows():
        item = row.to_dict()
        message = generate_email(item)
        rows.append({
            "rank": item.get("rank"),
            "company": item.get("company"),
            "country": item.get("country"),
            "buyer_type": item.get("buyer_type"),
            "decision_maker": item.get("decision_maker"),
            "decision_title": item.get("decision_title"),
            "email": item.get("email"),
            "email_quality_score": item.get("email_quality_score"),
            "customer_probability": item.get("customer_probability"),
            "buyer_class": item.get("buyer_class"),
            "subject": message["subject"],
            "email_body": message["email_body"],
            "follow_up_1": message["follow_up_1"],
            "follow_up_2": message["follow_up_2"],
            "linkedin_message": message["linkedin_message"],
        })
    return pd.DataFrame(rows)


st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {direction:rtl;text-align:right}
.block-container{max-width:1650px;padding-top:1rem}
.hero{background:linear-gradient(130deg,#0a0c0d 0%,#171b1c 56%,#332a16 100%);border:1px solid #725d2a;border-radius:24px;padding:28px 30px;margin-bottom:16px;box-shadow:0 14px 44px rgba(0,0,0,.27)}
.hero h1{margin:0;color:#fff;font-size:2.35rem}.hero p{margin:.55rem 0 0;color:#ddd2b6;font-size:1.02rem}.gold{color:#e8c76b}
.good{background:#14281d;border-right:4px solid #45be7b;padding:14px 16px;border-radius:12px;margin:.5rem 0 1rem}
.warn{background:#312812;border-right:4px solid #e0b256;padding:14px 16px;border-radius:12px;margin:.5rem 0 1rem}
[data-testid="stMetric"]{border:1px solid #34383b;border-radius:16px;padding:12px}
.small-note{font-size:.88rem;color:#b9b2a3}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
<h1>STYLE <span class="gold">Golden 500 Buyer Intelligence OS</span></h1>
<p>ملف العملاء أو بحث مباشر → أصحاب القرار → أفضل Email → قوة العميل → سرعة الوصول → نية الشراء التقديرية → رسالة إنجليزية مخصصة لكل دولة</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="good">
<b>هدف اليوم الأول:</b> ترتيب أقوى الحسابات القابلة للتواصل أولًا، ثم إعطاء فريق المبيعات الرسالة المناسبة لكل سوق بدل إرسال رسالة واحدة للجميع.
</div>
""", unsafe_allow_html=True)

serper_key = secret("SERPER_API_KEY")
apollo_key = secret("APOLLO_API_KEY")

with st.sidebar:
    st.markdown("## STYLE Golden 500")
    source_mode = st.radio("مصدر العملاء", ["📂 تحليل ملف عندي", "🌍 بحث مباشر من السوق"])
    st.divider()
    st.caption("API Status")
    st.write("Serper:", "✅ READY" if serper_key else "❌ MISSING")
    st.write("Apollo:", "✅ READY" if apollo_key else "❌ MISSING")

    with st.expander("Streamlit Secrets"):
        st.code(
            'SERPER_API_KEY = "YOUR_SERPER_KEY"\nAPOLLO_API_KEY = "YOUR_APOLLO_KEY"',
            language="toml",
        )
        st.caption("المفاتيح لا تُكتب داخل GitHub.")

if source_mode == "📂 تحليل ملف عندي":
    st.subheader("تحليل ملف العملاء واستخراج أقوى 500 فرصة")
    st.caption("ارفع CSV أو Excel. النظام يحاول التعرف تلقائيًا على Company / Website / Country / Email / Phone / Contact / Job Title.")

    uploaded = st.file_uploader("ارفع ملف العملاء", type=["csv", "xlsx", "xls"])
    c1, c2, c3 = st.columns(3)
    max_rows = c1.slider("أقصى عدد يتم تحليله", 50, 500, 500, 50)
    use_apollo = c2.toggle("استخدم Apollo لأصحاب القرار والإيميلات الناقصة", value=True)
    only_business_email = c3.toggle("رتّب Business Emails فوق العام", value=True)

    if uploaded is not None:
        try:
            raw = read_upload(uploaded)
            st.write(f"تم قراءة **{len(raw):,}** صف.")
            with st.expander("معاينة الملف", expanded=False):
                st.dataframe(raw.head(30), use_container_width=True, hide_index=True)

            if st.button("🔥 حلّل الملف وابنِ Golden 500", type="primary", use_container_width=True):
                if use_apollo and not apollo_key:
                    st.error("Apollo مطلوب لأن اختيار Apollo مفعّل. أضف APOLLO_API_KEY في Streamlit Secrets أو اقفل الاختيار.")
                else:
                    with st.spinner("جاري تنظيف البيانات، فحص المواقع، تقييم الإيميلات، البحث عن أصحاب القرار وترتيب الفرص..."):
                        buyers = analyze_uploaded_file(
                            raw,
                            apollo_api_key=apollo_key,
                            max_rows=max_rows,
                            use_apollo=use_apollo,
                        )
                    if only_business_email and not buyers.empty:
                        buyers = buyers.sort_values(
                            ["email_quality_score", "customer_probability", "buyer_score"],
                            ascending=False,
                        ).reset_index(drop=True)
                        buyers["rank"] = range(1, len(buyers) + 1)
                    st.session_state["golden_buyers"] = buyers
                    st.success(f"تم تحليل وترتيب {len(buyers):,} حساب.")
        except Exception as exc:
            st.error(f"تعذر قراءة/تحليل الملف: {exc}")

else:
    st.subheader("بحث مباشر عن أقوى المشترين")
    st.caption("البحث المباشر يستخدم Serper لاكتشاف الشركات وApollo للبحث عن أصحاب القرار. عدد النتائج الفعلي يعتمد على نتائج البحث وحدود الـAPI.")

    a1, a2 = st.columns(2)
    countries = a1.multiselect("اختار الدول", COUNTRIES, default=COUNTRIES)
    buyer_types = a2.multiselect(
        "نوع العميل",
        BUYER_TYPES,
        default=["Importer", "Distributor", "Wholesaler", "Fabricator"],
    )

    b1, b2 = st.columns(2)
    materials = b1.multiselect("الخامات الخمسة", MATERIALS, default=MATERIALS, max_selections=5)
    target = b2.slider("عدد العملاء المطلوب", 50, 500, 500, 50)

    c1, c2 = st.columns(2)
    depth = c1.select_slider("عمق البحث", options=[1, 2, 3], value=2)
    apollo_budget = c2.slider(
        "أقصى عدد Apollo Email Enrichments",
        0,
        500,
        100,
        25,
        help="اجعله حسب رصيد Apollo. البحث عن الأشخاص شيء مختلف عن كشف Email المدفوع بالرصيد.",
    )

    if st.button("🚀 ابحث وابنِ Golden Buyers", type="primary", use_container_width=True):
        if not serper_key:
            st.error("SERPER_API_KEY غير موجود في Streamlit Secrets.")
        elif not apollo_key:
            st.error("APOLLO_API_KEY غير موجود في Streamlit Secrets.")
        elif not countries or not buyer_types or not materials:
            st.error("اختار دولة ونوع عميل وخامة واحدة على الأقل.")
        else:
            with st.spinner("جاري اكتشاف الشركات، التحقق من المواقع، البحث عن أصحاب القرار وتقييم احتمالية العميل..."):
                try:
                    buyers = build_golden500(
                        countries=countries,
                        buyer_types=buyer_types,
                        materials=materials,
                        serper_api_key=serper_key,
                        apollo_api_key=apollo_key,
                        target=target,
                        search_depth=depth,
                        email_enrichment_budget=apollo_budget,
                    )
                    st.session_state["golden_buyers"] = buyers
                    st.success(f"تم بناء {len(buyers):,} نتيجة قابلة للترتيب من النتائج التي أمكن التحقق منها.")
                except Exception as exc:
                    st.error(f"حصل خطأ أثناء البحث: {exc}")


buyers = st.session_state.get("golden_buyers", pd.DataFrame())

if not buyers.empty:
    st.divider()
    st.subheader("Golden Buyer Ranking")

    for col in ["customer_probability", "buyer_score", "email_quality_score", "decision_access", "company_strength"]:
        if col in buyers.columns:
            buyers[col] = pd.to_numeric(buyers[col], errors="coerce").fillna(0)

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Total", len(buyers))
    k2.metric("Golden", int((buyers.get("buyer_class", "") == "GOLDEN").sum()))
    k3.metric("A-Class", int((buyers.get("buyer_class", "") == "A-CLASS").sum()))
    k4.metric("Strong Emails ≥80", int((buyers.get("email_quality_score", 0) >= 80).sum()))
    k5.metric("Decision Makers", int(buyers.get("decision_maker", pd.Series(dtype=str)).fillna("").astype(str).str.len().gt(2).sum()))
    k6.metric("High Probability ≥80", int((buyers.get("customer_probability", 0) >= 80).sum()))

    f1, f2, f3, f4 = st.columns(4)
    country_options = sorted(buyers["country"].dropna().astype(str).unique().tolist()) if "country" in buyers else []
    type_options = sorted(buyers["buyer_type"].dropna().astype(str).unique().tolist()) if "buyer_type" in buyers else []
    country_filter = f1.multiselect("الدولة", country_options)
    type_filter = f2.multiselect("نوع العميل", type_options)
    min_strength = f3.slider("قوة العميل", 0, 100, 60)
    min_probability = f4.slider("احتمالية التحول لعميل", 0, 100, 60)

    g1, g2 = st.columns(2)
    min_email = g1.slider("قوة الإيميل", 0, 100, 50)
    quick_access_only = g2.toggle("أظهر الأسرع وصولًا أولًا", value=True)

    view = buyers.copy()
    if country_filter:
        view = view[view["country"].isin(country_filter)]
    if type_filter:
        view = view[view["buyer_type"].isin(type_filter)]
    if "company_strength" in view:
        view = view[view["company_strength"] >= min_strength]
    if "customer_probability" in view:
        view = view[view["customer_probability"] >= min_probability]
    if "email_quality_score" in view:
        view = view[view["email_quality_score"] >= min_email]

    sort_cols = [c for c in ["customer_probability", "email_quality_score", "decision_access", "buyer_score"] if c in view.columns]
    if quick_access_only and sort_cols:
        view = view.sort_values(sort_cols, ascending=False)

    columns = [
        "rank", "company", "country", "buyer_type", "buyer_class",
        "customer_probability", "probability_band", "buyer_score", "company_strength",
        "decision_maker", "decision_title", "decision_access",
        "email", "email_quality_score", "email_quality", "email_source",
        "whatsapp", "phone", "website", "linkedin_url",
        "style_fit", "import_signal", "project_signal", "repeat_potential",
        "why_ranked", "last_verified",
    ]
    columns = [c for c in columns if c in view.columns]

    st.dataframe(
        view[columns],
        use_container_width=True,
        hide_index=True,
        height=680,
        column_config={
            "website": st.column_config.LinkColumn("Website", display_text="Open"),
            "linkedin_url": st.column_config.LinkColumn("LinkedIn", display_text="Open"),
            "customer_probability": st.column_config.ProgressColumn("Customer Probability", min_value=0, max_value=100, format="%.1f"),
            "email_quality_score": st.column_config.ProgressColumn("Email Quality", min_value=0, max_value=100, format="%.0f"),
            "buyer_score": st.column_config.ProgressColumn("Buyer Score", min_value=0, max_value=100, format="%.1f"),
        },
    )

    st.markdown("### الرسالة الإنجليزية المخصصة لكل دولة")
    if not view.empty:
        labels = [f"#{int(r.get('rank', i+1))} — {r.get('company','')} — {r.get('country','')}" for i, r in view.reset_index(drop=True).iterrows()]
        selected_label = st.selectbox("اختار العميل", labels)
        selected_idx = labels.index(selected_label)
        selected = view.reset_index(drop=True).iloc[selected_idx].to_dict()
        campaign = generate_email(selected)

        q1, q2, q3, q4 = st.columns(4)
        q1.metric("Probability", f"{selected.get('customer_probability', 0):.1f}%")
        q2.metric("Email Quality", f"{selected.get('email_quality_score', 0):.0f}/100")
        q3.metric("Buyer Score", f"{selected.get('buyer_score', 0):.1f}/100")
        q4.metric("Decision Access", f"{selected.get('decision_access', 0):.0f}/100")

        st.markdown("#### Subject")
        st.code(campaign["subject"], language=None)
        st.markdown("#### First Email")
        st.code(campaign["email_body"], language=None)

        t1, t2, t3 = st.tabs(["Follow-up 1", "Follow-up 2", "LinkedIn"])
        with t1:
            st.code(campaign["follow_up_1"], language=None)
        with t2:
            st.code(campaign["follow_up_2"], language=None)
        with t3:
            st.code(campaign["linkedin_message"], language=None)

    st.markdown("### تنزيل النتائج والحملات")
    export_campaigns = campaign_export(view)
    d1, d2, d3 = st.columns(3)
    d1.download_button(
        "Download Ranked Buyers CSV",
        view.to_csv(index=False).encode("utf-8-sig"),
        "style_golden_buyers_ranked.csv",
        "text/csv",
        use_container_width=True,
    )
    d2.download_button(
        "Download Ranked Buyers Excel",
        excel_bytes(view, "Ranked Buyers"),
        "style_golden_buyers_ranked.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
    d3.download_button(
        "Download Emails + Follow-ups",
        excel_bytes(export_campaigns, "Campaigns"),
        "style_country_campaigns.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    st.markdown("""
    <div class="warn">
    <b>مهم:</b> Customer Probability وBuyer Score أدوات ترتيب تجاري مبنية على إشارات متاحة وليست ضمانًا للشراء أو الرد.
    الإيميل الأقوى هو الأعلى من حيث تطابق الدومين، MX، دور صاحب القرار ومصدر التحقق. لا يتم اعتبار رقم الهاتف WhatsApp إلا إذا ظهر كـWhatsApp في مصدر عام.
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("ابدأ برفع ملف العملاء أو تشغيل البحث المباشر. بعد التحليل سيظهر الترتيب والرسائل هنا.")
