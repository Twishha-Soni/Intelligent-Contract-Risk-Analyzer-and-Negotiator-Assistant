# streamlit_app.py

import streamlit as st
import requests

API_URL = "http://localhost:8000"

# -------------------- Page Config --------------------
st.set_page_config(
    page_title="Contract Risk Analyzer",
    page_icon="⚖️",
    layout="wide"
)

# -------------------- Custom CSS --------------------
st.markdown("""
<style>
.stApp {
    background-color: black;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

h1 {
    color: #1f3b73;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 12px;
    border: 1px solid #dbe3ef;
    background: white;
    padding: 15px;
}
</style>
""", unsafe_allow_html=True)

# -------------------- Session State --------------------
if "playbook_ingested" not in st.session_state:
    st.session_state["playbook_ingested"] = False

# -------------------- Title --------------------
st.title("⚖️ Contract Risk Analyzer & Negotiator")
st.markdown("---")

# ==================== Upload Section ====================
left, right = st.columns(2, gap="large")

# -------------------- Playbook --------------------
with left:
    with st.container(border=True):
        st.subheader("📘 Playbook")

        playbook_file = st.file_uploader(
            "Upload Playbook (PDF)",
            type=["pdf"],
            key="playbook_uploader"
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "📥 Ingest",
                use_container_width=True,
                disabled=playbook_file is None
            ):
                with st.spinner("Ingesting playbook..."):
                    resp = requests.post(
                        f"{API_URL}/playbook/upload",
                        files={
                            "file": (
                                playbook_file.name,
                                playbook_file.getvalue()
                            )
                        },
                    )

                    if resp.ok:
                        st.session_state["playbook_ingested"] = True
                        st.success("✅ Playbook Ready")
                    else:
                        st.error(resp.text)

        with col2:
            if st.button(
                "🗑 Remove",
                use_container_width=True,
                disabled=not st.session_state["playbook_ingested"]
            ):
                resp = requests.delete(f"{API_URL}/playbook")

                if resp.ok:
                    st.session_state["playbook_ingested"] = False
                    st.session_state.pop("clauses", None)
                    st.session_state.pop("contract_id", None)
                    st.success("Playbook Removed")
                else:
                    st.error(resp.text)

# -------------------- Contract --------------------
with right:
    with st.container(border=True):
        st.subheader("📄 Contract")

        uploaded = st.file_uploader(
            "Upload Contract",
            type=["pdf", "docx"]
        )

        if not st.session_state["playbook_ingested"]:
            st.info("📘 Please ingest a playbook first.")

        if uploaded and st.button(
            "🔍 Analyze",
            use_container_width=True,
        ):
            with st.spinner("Analyzing contract..."):
                resp = requests.post(
                    f"{API_URL}/contracts/analyze",
                    files={
                        "file": (
                            uploaded.name,
                            uploaded.getvalue()
                        )
                    },
                )

            if resp.ok:
                data = resp.json()
                st.session_state["contract_id"] = data["contract_id"]
                st.session_state["clauses"] = data["clauses"]
                st.success("✅ Analysis Complete")
            else:
                st.error(resp.text)

st.markdown("<br>", unsafe_allow_html=True)

# ==================== Negotiation Summary ====================
with st.container(border=True):
    st.subheader("⚖️ Negotiation Summary")

    if "clauses" not in st.session_state:
        st.info("Upload and analyze a contract to generate the negotiation brief.")
    else:
        contract_id = st.session_state["contract_id"]

        if st.button(
            "📄 Generate Negotiation Brief",
            use_container_width=True
        ):
            resp = requests.get(
                f"{API_URL}/contracts/{contract_id}/brief"
            )

            if resp.ok:
                st.download_button(
                    "⬇️ Download Brief PDF",
                    data=resp.content,
                    file_name=f"negotiation_brief_{contract_id}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            else:
                st.error(resp.text)