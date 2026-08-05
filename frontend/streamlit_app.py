# streamlit_app.py
import streamlit as st
import requests

API_URL = "http://localhost:8000"

st.title("Contract Risk Analyzer")

uploaded = st.file_uploader("Upload contract", type=["pdf", "docx"])

if uploaded and st.button("Analyze"):
    with st.spinner("Analyzing clauses..."):
        resp = requests.post(
            f"{API_URL}/contracts/analyze",
            files={"file": (uploaded.name, uploaded.getvalue())},
        )
    if resp.ok:
        data = resp.json()
        st.session_state["contract_id"] = data["contract_id"]
        st.session_state["clauses"] = data["clauses"]
    else:
        st.error(resp.text)

if "clauses" in st.session_state:
    contract_id = st.session_state["contract_id"]

    if st.button("Generate Negotiation Brief"):
        resp = requests.get(f"{API_URL}/contracts/{contract_id}/brief")
        if resp.ok:
            st.download_button("Download Brief PDF", resp.content, file_name="negotiation_brief_{contract_id}.pdf")
        else:
            st.error(resp.text)