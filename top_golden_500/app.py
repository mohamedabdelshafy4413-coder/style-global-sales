from __future__ import annotations

import os
from io import BytesIO

import pandas as pd
import streamlit as st

from core.file_intelligence import parse_many
from core.scoring import score_dataframe, TARGET_COUNTRIES
from core.email_engine import PRODUCTS, personalize_dataframe
from core.enrichment import enrich_row_with_apollo

st.set_page_config(
    page_title="TOP GOLDEN 500",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded",
)


def secret(name: str) -> str:
    try:
        value = st.secrets.get(name, "")
        if value:
            return str(value)
    except Exception:
        pass
    return os.getenv(name, "")


def to_excel(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="TOP GOLDEN 500")
    return output.getvalue()


st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {direction: rtl; text-align: right;}
.block-container {max-width: 1700px; padding-top: 1rem;}
.hero {background:linear-gradient(120deg,#090b0c,#17191a 60%,#332914);border:1px solid #7d6633;border-radius:26px;padding:30px;margin-bottom:18px;box-shadow:0 18px 50px rgba(0,0,0,.30)}
.hero h1{margin:0;color:#fff;font-size:2.7rem}.hero .gold{color:#e8c86e}.hero p{color:#d8cfba;font-size:1.05rem;margin:.6rem 0 0}
.badge{display:inline-block;padding:5px 10px;border:1px solid #7d6633;border-radius:999px;color:#e8c86e;margin-left:8px}
[data-testid="stMetric"]{border:1px solid #34383b;border-radius:18px;padding:12px}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
<span class="badge">STYLE EXPORT INTELLIGENCE</span>
<h1>TOP <span class="gold">GOLDEN 500</span></h1>
<p>Upload → Clean → Score → Rank → Personalize → Export</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("## 🎯 Targeting")
selected_countries = st.sidebar.multiselect("الدول المستهدفة", TARGET_COUNTRIES, default=TARGET_COUNTRIES)
selected_types = st.sidebar.multiselect(
    "نوع العميل",
    ["Importer", "Distributor", "Wholesaler", "Stone Fabricator", "Architectural Supplier", "Contractor", "Developer", "Tile & Stone Showroom", "Hotel Supplier", "Other"],
    default=["Importer", "Distributor", "Wholesaler", "Stone Fabricator", "Architectural Supplier", "Contractor", "Developer"],
)
selected_products = st.sidebar.multiselect("الخامات الخمس", list(PRODUCTS.keys()), default=list(PRODUCTS.keys()), max_selections=5)
min_probability = st.sidebar.slider("أقل احتمالية ليصبح عميل", 0, 100, 60)
max_results = st.sidebar.slider("عدد النتائج", 50, 500, 500, 50)
avg_first_order = st.sidebar.number_input("متوسط قيمة أول أوردر ($) — تقدير", min_value=0, value=15000, step=1000)
gross_margin = st.sidebar.slider("هامش الربح المتوقع % — تقدير", 0, 60, 18)

st.markdown("### 1) ارفع ملفات العملاء")
files = st.file_uploader(
    "Excel / CSV / Word / text-based PDF — يمكن رفع أكثر من ملف",
    type=["xlsx", "xlsm", "xls", "csv", "docx", "pdf"],
    accept_multiple_files=True,
)

apollo_key = secret("APOLLO_API_KEY")
serper_key = secret("SERPER_API_KEY")
col1, col2, col3 = st.columns(3)
col1.metric("Apollo", "READY" if apollo_key else "OPTIONAL / MISSING")
col2.metric("Serper", "READY" if serper_key else "OPTIONAL / MISSING")
col3.metric("Mode", "FILE INTELLIGENCE")

with st.expander("Streamlit Secrets"):
    st.code('APOLLO_API_KEY = "YOUR_KEY"\nSERPER_API_KEY = "YOUR_KEY"', language="toml")
    st.caption("لا تضع أي API key داخل GitHub. ضعه فقط في Streamlit Secrets.")

enrich = st.checkbox(
    "استخدم Apollo للبحث عن Decision Maker عند غياب الاسم/الوظيفة",
    value=False,
    disabled=not bool(apollo_key),
    help="يفضل تشغيله على أقوى الحسابات فقط للحفاظ على حدود الـAPI.",
)

analyze = st.button("🔥 ANALYZE & BUILD TOP GOLDEN 500", type="primary", use_container_width=True)

if analyze:
    if not files:
        st.error("ارفع ملف واحد على الأقل.")
    else:
        with st.spinner("جاري قراءة الملفات وتنظيف الداتا..."):
            try:
                raw = parse_many(files)
            except Exception as exc:
                st.error(f"تعذر قراءة الملف: {exc}")
                raw = pd.DataFrame()

        if not raw.empty:
            st.session_state["raw_count"] = len(raw)

            if enrich and apollo_key:
                preliminary = score_dataframe(raw)
                candidates = preliminary[
                    (preliminary["contact_name"].fillna("").str.len() < 2)
                    | (preliminary["job_title"].fillna("").str.len() < 2)
                ].head(100)
                records = raw.to_dict("records")
                for original_index in candidates.index.tolist():
                    if original_index < len(records):
                        records[original_index] = enrich_row_with_apollo(records[original_index], apollo_key)
                raw = pd.DataFrame(records)

            scored = score_dataframe(raw)
            if selected_countries:
                scored = scored[scored["country"].isin(selected_countries) | scored["country"].eq("")]
            if selected_types:
                scored = scored[scored["customer_type"].isin(selected_types)]
            scored = scored[scored["customer_probability"] >= min_probability]
            scored = scored.sort_values(
                ["customer_probability", "reply_speed", "reachability", "buying_intent"],
                ascending=False,
            ).head(max_results).reset_index(drop=True)
            if not scored.empty:
                scored["rank"] = range(1, len(scored) + 1)
            st.session_state["golden"] = personalize_dataframe(scored, selected_products)


df = st.session_state.get("golden", pd.DataFrame())

if df.empty:
    st.info("بعد رفع الملفات اضغط ANALYZE. النظام سيبني ترتيب أقوى العملاء من البيانات الموجودة فعليًا في ملفاتك.")
else:
    total = len(df)
    golden = int((df["buyer_class"] == "GOLDEN").sum())
    aclass = int((df["buyer_class"] == "A-CLASS").sum())
    avg_prob = round(df["customer_probability"].mean(), 1)
    weighted_revenue = float((df["customer_probability"] / 100 * avg_first_order).sum())
    expected_profit = weighted_revenue * gross_margin / 100

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Top Contacts", total)
    m2.metric("Golden", golden)
    m3.metric("A-Class", aclass)
    m4.metric("Avg Probability", f"{avg_prob}%")
    m5.metric("Weighted Pipeline*", f"${weighted_revenue:,.0f}")
    m6.metric("Expected Gross Profit*", f"${expected_profit:,.0f}")
    st.caption("* Strategic estimate based on your average first-order value and gross-margin assumptions; not a guaranteed forecast.")

    st.markdown("### 2) TOP GOLDEN 500 Ranking")
    columns = [
        "rank", "company", "country", "customer_type", "contact_name", "job_title", "email", "phone", "website",
        "buyer_class", "customer_probability", "buying_intent", "reply_speed", "reachability",
        "company_strength", "style_fit", "email_quality", "email_status", "source_file",
    ]
    columns = [c for c in columns if c in df.columns]
    st.dataframe(
        df[columns],
        use_container_width=True,
        hide_index=True,
        height=650,
        column_config={
            "website": st.column_config.LinkColumn("Website", display_text="Open"),
            "customer_probability": st.column_config.ProgressColumn("Customer Probability", min_value=0, max_value=100),
            "buying_intent": st.column_config.ProgressColumn("Buying Intent", min_value=0, max_value=100),
            "reply_speed": st.column_config.ProgressColumn("Reply Speed", min_value=0, max_value=100),
            "reachability": st.column_config.ProgressColumn("Reachability", min_value=0, max_value=100),
        },
    )

    st.markdown("### 3) الرسالة المخصصة لكل عميل")
    choice = st.selectbox(
        "اختار العميل",
        options=list(range(len(df))),
        format_func=lambda i: f"#{int(df.iloc[i]['rank'])} — {df.iloc[i].get('company', '')} — {df.iloc[i].get('contact_name', '') or 'Decision Maker'}",
    )
    row = df.iloc[choice]
    st.text_input("Subject", row.get("email_subject", ""))
    st.text_area("First Email", row.get("email_message", ""), height=340)
    f1, f2 = st.columns(2)
    f1.text_area("Follow-up 1", row.get("followup_1", ""), height=240)
    f2.text_area("Follow-up 2", row.get("followup_2", ""), height=240)

    st.markdown("### 4) Export")
    e1, e2 = st.columns(2)
    e1.download_button(
        "Download TOP GOLDEN 500 CSV",
        df.to_csv(index=False).encode("utf-8-sig"),
        "TOP_GOLDEN_500.csv",
        "text/csv",
        use_container_width=True,
    )
    e2.download_button(
        "Download TOP GOLDEN 500 Excel",
        to_excel(df),
        "TOP_GOLDEN_500.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    st.warning(
        "Probability, Reply Speed and Buying Intent are prioritization scores based on the uploaded data. "
        "They are not guarantees of reply, purchase, profit or conversion. Verified shipment/import data is required for true historical buying-volume ranking."
    )
