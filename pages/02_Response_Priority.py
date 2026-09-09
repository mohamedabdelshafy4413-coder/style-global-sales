from __future__ import annotations

import pandas as pd
import streamlit as st

from core.scoring_engine import response_likelihood

st.set_page_config(page_title="Response Priority | STYLE", page_icon="⚡", layout="wide")

st.markdown("## ⚡ Response Priority — مين نكلمه الأول؟")
st.caption("يرتب الحسابات حسب تقدير سرعة الوصول والرد، جودة الإيميل، قوة صاحب القرار واحتمالية التحول لعميل. التقييم ترتيب تجاري وليس ضمانًا للرد أو الشراء.")

buyers = st.session_state.get("golden_buyers", pd.DataFrame())
if buyers.empty:
    st.info("ارجع للصفحة الرئيسية، ارفع ملف العملاء أو شغّل البحث أولًا.")
    st.stop()

view = buyers.copy()
view["response_likelihood"] = view.apply(lambda row: response_likelihood(row.to_dict()), axis=1)

for col in ["customer_probability", "buyer_score", "email_quality_score", "decision_access", "response_likelihood"]:
    if col in view.columns:
        view[col] = pd.to_numeric(view[col], errors="coerce").fillna(0)

c1,c2,c3,c4 = st.columns(4)
min_reply = c1.slider("أقل احتمالية رد سريع", 0, 100, 65)
min_buy = c2.slider("أقل احتمالية عميل", 0, 100, 65)
min_email = c3.slider("أقل قوة Email", 0, 100, 60)
only_dm = c4.toggle("Decision maker فقط", value=True)

filtered = view[
    (view["response_likelihood"] >= min_reply)
    & (view["customer_probability"] >= min_buy)
    & (view["email_quality_score"] >= min_email)
].copy()
if only_dm and "decision_maker" in filtered.columns:
    filtered = filtered[filtered["decision_maker"].fillna("").astype(str).str.len() > 2]

filtered = filtered.sort_values(
    ["response_likelihood", "customer_probability", "email_quality_score", "decision_access"],
    ascending=False,
).reset_index(drop=True)
filtered["priority_rank"] = range(1, len(filtered) + 1)

k1,k2,k3,k4 = st.columns(4)
k1.metric("Fast-response targets", len(filtered))
k2.metric("Reply Score ≥80", int((filtered["response_likelihood"] >= 80).sum()))
k3.metric("Customer Probability ≥80", int((filtered["customer_probability"] >= 80).sum()))
k4.metric("Strong Email ≥80", int((filtered["email_quality_score"] >= 80).sum()))

cols = [
    "priority_rank", "company", "country", "buyer_type", "decision_maker", "decision_title",
    "email", "email_quality_score", "response_likelihood", "customer_probability",
    "buyer_score", "decision_access", "whatsapp", "phone", "website", "why_ranked"
]
cols = [c for c in cols if c in filtered.columns]

st.dataframe(
    filtered[cols],
    use_container_width=True,
    hide_index=True,
    height=720,
    column_config={
        "website": st.column_config.LinkColumn("Website", display_text="Open"),
        "response_likelihood": st.column_config.ProgressColumn("Fast Reply Score", min_value=0, max_value=100, format="%.1f"),
        "customer_probability": st.column_config.ProgressColumn("Customer Probability", min_value=0, max_value=100, format="%.1f"),
        "email_quality_score": st.column_config.ProgressColumn("Email Quality", min_value=0, max_value=100, format="%.0f"),
    },
)

st.download_button(
    "Download Fastest Priority List",
    filtered.to_csv(index=False).encode("utf-8-sig"),
    "style_fast_response_priority.csv",
    "text/csv",
    use_container_width=True,
)
