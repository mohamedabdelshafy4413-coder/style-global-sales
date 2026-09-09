from __future__ import annotations

import os
from io import BytesIO

import pandas as pd
import streamlit as st

from core.engine import build_top50

st.set_page_config(page_title="STYLE Buyer Command Center", page_icon="🎯", layout="wide", initial_sidebar_state="expanded")

DEFAULT_COUNTRIES = ["Saudi Arabia","United Arab Emirates","Morocco","United Kingdom","United States","France","Germany","Italy","Spain","Canada"]
DEFAULT_MATERIALS = ["Galala Light","Sunny Light","Meli Brown","Meli Grey","Zafarana Flower"]

def secret(name: str) -> str:
    try:
        value = st.secrets.get(name, "")
        if value: return value
    except Exception:
        pass
    return os.getenv(name, "")

def excel_bytes(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Top50 Buyers")
    return output.getvalue()

st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {direction:rtl;text-align:right}
.block-container{max-width:1600px;padding-top:1.1rem}
.hero{background:linear-gradient(130deg,#0b0d0e 0%,#171b1c 55%,#2f291c 100%);border:1px solid #6f5c2c;border-radius:24px;padding:28px 30px;margin-bottom:18px;box-shadow:0 12px 38px rgba(0,0,0,.24)}
.hero h1{margin:0;color:#fff;font-size:2.35rem}.hero p{margin:.55rem 0 0;color:#d8cfb8;font-size:1.03rem}.gold{color:#e6c86e}
.good{background:#14291e;border-right:4px solid #45be7b;padding:14px 16px;border-radius:12px}.warn{background:#322914;border-right:4px solid #e0b256;padding:14px 16px;border-radius:12px}
[data-testid="stMetric"]{border:1px solid #34383b;border-radius:16px;padding:12px}
</style>
""", unsafe_allow_html=True)

st.markdown("""<div class="hero"><h1>STYLE <span class="gold">Buyer Command Center</span></h1><p>اكتشاف أقوى المشترين المحتملين → Decision Makers → Emails → WhatsApp/Phones العامة → ترتيب فرصة الشراء</p></div>""", unsafe_allow_html=True)
st.markdown("""<div class="good"><b>المهمة:</b> بناء قائمة Top 50 قابلة للتنفيذ التجاري من الدول العشر للخامات المختارة، مع فصل واضح بين بيانات عامة تم العثور عليها وبين بيانات Apollo enrichment.</div>""", unsafe_allow_html=True)

st.sidebar.markdown("## إعداد البحث")
materials = st.sidebar.multiselect("الخمس خامات", DEFAULT_MATERIALS, default=DEFAULT_MATERIALS, max_selections=5)
countries = st.sidebar.multiselect("الدول", DEFAULT_COUNTRIES, default=DEFAULT_COUNTRIES)
email_credit_limit = st.sidebar.slider("Apollo Email Enrichment Credits", 0, 50, 15, 5, help="People Search في Apollo لا يكشف Email. هذا الرقم يحدد أقصى عدد من أقوى الأشخاص الذين نحاول Enrich لهم Email.")
serper_key = secret("SERPER_API_KEY"); apollo_key = secret("APOLLO_API_KEY")
s1, s2 = st.columns(2); s1.metric("Serper", "READY" if serper_key else "MISSING"); s2.metric("Apollo", "READY" if apollo_key else "MISSING")
with st.expander("إعداد مفاتيح Streamlit Secrets"):
    st.code('SERPER_API_KEY = "YOUR_SERPER_KEY"\nAPOLLO_API_KEY = "YOUR_APOLLO_KEY"', language="toml")
    st.caption("لا تضع المفاتيح داخل GitHub أو app.py. أضفها من Streamlit App Settings → Secrets.")

run = st.button("🚀 ابحث وابنِ أقوى 50 Buyer", type="primary", use_container_width=True)
if run:
    if not serper_key: st.error("SERPER_API_KEY غير موجود في Streamlit Secrets.")
    elif not apollo_key: st.error("APOLLO_API_KEY غير موجود في Streamlit Secrets.")
    elif not countries or not materials: st.error("اختار دولة وخامة واحدة على الأقل.")
    else:
        with st.spinner("جاري اكتشاف الشركات، فحص مواقعها العامة، البحث عن Decision Makers في Apollo، ثم ترتيب أقوى الفرص..."):
            try:
                st.session_state["buyers"] = build_top50(countries, materials, serper_key, apollo_key, email_credit_limit)
            except Exception as exc:
                st.session_state["buyers"] = pd.DataFrame(); st.error(f"حصل خطأ أثناء البحث: {exc}")

buyers = st.session_state.get("buyers", pd.DataFrame())
if buyers.empty:
    st.info("اضغط زر البحث لبناء Top 50. أول تشغيل قد يأخذ بعض الوقت لأن النظام يفحص مصادر متعددة.")
else:
    k1,k2,k3,k4,k5 = st.columns(5)
    k1.metric("Buyers", len(buyers)); k2.metric("Golden", int((buyers["buyer_class"]=="GOLDEN").sum()))
    k3.metric("Emails", int(buyers["email"].fillna("").astype(str).str.len().gt(3).sum()))
    k4.metric("Decision Makers", int(buyers["decision_maker"].fillna("").astype(str).str.len().gt(2).sum()))
    k5.metric("WhatsApp", int(buyers["whatsapp"].fillna("").astype(str).str.len().gt(5).sum()))
    f1,f2,f3 = st.columns(3)
    country_filter = f1.multiselect("فلتر الدولة", sorted(buyers["country"].dropna().unique().tolist()))
    class_filter = f2.multiselect("فلتر القوة", ["GOLDEN","A-CLASS","HIGH POTENTIAL","RESEARCH"])
    min_score = f3.slider("Minimum Score", 0, 100, 60)
    view = buyers.copy()
    if country_filter: view = view[view["country"].isin(country_filter)]
    if class_filter: view = view[view["buyer_class"].isin(class_filter)]
    view = view[view["opportunity_score"] >= min_score]
    columns = ["rank","company","country","materials","buyer_class","opportunity_score","decision_maker","decision_title","email","email_source","whatsapp","phone","website","importer_signal","scale_signal","project_signal","material_fit","why_ranked","evidence_url","last_verified"]
    columns = [c for c in columns if c in view.columns]
    st.markdown("### Top Buyer Ranking")
    st.dataframe(view[columns], use_container_width=True, hide_index=True, height=690, column_config={
        "website": st.column_config.LinkColumn("Website", display_text="Open"),
        "evidence_url": st.column_config.LinkColumn("Evidence", display_text="Source"),
        "opportunity_score": st.column_config.ProgressColumn("Purchase Opportunity", min_value=0, max_value=100, format="%.1f"),
    })
    d1,d2 = st.columns(2)
    d1.download_button("Download CSV", buyers.to_csv(index=False).encode("utf-8-sig"), "style_top50_buyers.csv", "text/csv", use_container_width=True)
    d2.download_button("Download Excel", excel_bytes(buyers), "style_top50_buyers.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    st.markdown("""<div class="warn"><b>مهم:</b> Opportunity Score هو ترتيب بحث ومبيعات وليس إثباتًا لحجم مشتريات تاريخي. للحصول على Ranking مبني على الشحنات الفعلية نحتاج لاحقًا Import/Shipment Database. كذلك رقم الهاتف لا يُصنف WhatsApp إلا إذا ظهر كـWhatsApp في مصدر عام.</div>""", unsafe_allow_html=True)
