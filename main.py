import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from app.azureClient import fetch_azure_costs_last_30d
from app.recommender import generate_recommendations
from app.utils import currency, kpis

load_dotenv()

st.set_page_config(page_title="Azure Cost Optimization Agent", layout="wide")

st.title("💸 Azure Cost Optimization Agent (MVP)")
st.caption("Analyze costs, flag waste, and estimate savings. Works with sample data out of the box.")

# --- Data loading 
src = st.sidebar.radio("Data source", ["Sample (mock)", "Azure (later)"], index=0)
if src == "Sample (mock)":
    df = fetch_azure_costs_last_30d()
else:
    st.sidebar.info("Hook real Azure billing here once credentials are set.")
    df = fetch_azure_costs_last_30d()

st.sidebar.download_button("Download current CSV", df.to_csv(index=False).encode(), file_name="current_costs.csv")

# --- KPIs
total, by_rg, by_type = kpis(df)
c1, c2, c3 = st.columns(3)
c1.metric("Total monthly cost (sample)", currency(total))
c2.metric("Top RG (sample)", by_rg.index[0] if len(by_rg)>0 else "-", currency(by_rg.iloc[0] if len(by_rg)>0 else 0))
c3.metric("Top Resource Type (sample)", by_type.index[0] if len(by_type)>0 else "-", currency(by_type.iloc[0] if len(by_type)>0 else 0))

st.subheader("Cost by Resource Group")
st.bar_chart(by_rg)

st.subheader("Cost by Resource Type")
st.bar_chart(by_type)

# --- Recommendations
st.subheader("Optimization Recommendations")
recs = generate_recommendations(df)
if len(recs) == 0:
    st.success("No obvious waste detected in the dataset.")
else:
    st.dataframe(recs, use_container_width=True)

    est_total_save = recs["est_monthly_saving_usd"].sum()
    st.metric("Estimated monthly savings", currency(est_total_save))

    # Optional LLM summary if key present
    api_key = os.getenv("OPENAI_API_KEY", "")
    if api_key and st.toggle("Generate executive summary (LLM)"):
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        top = recs.head(8).to_dict(orient="records")
        prompt = (
            "You are a FinOps assistant. Summarize these cost optimization findings for an engineering leader. "
            "Provide 3-5 bullets with actions and estimated monthly savings. Keep it crisp.\n\n"
            f"Findings JSON:\n{top}"
        )
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content":prompt}],
            temperature=0.2,
        )
        st.markdown(resp.choices[0].message.content)

st.divider()
st.caption("MVP heuristics: idle VMs, unattached disks, storage tiering, SQL downsize, Savings Plan candidates.")
