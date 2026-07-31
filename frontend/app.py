import streamlit as st
import requests
import base64

BACKEND_URL = 'http://localhost:8080'

st.set_page_config(page_title='Contract Risk Analyzer', layout='wide')
st.title('Intelligent Contract Risk Analyzer')

if 'playbook_ingested' not in st.session_state:
    st.session_state.playbook_ingested = False
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None

# ---- Sidebar: Playbook ingestion ----
with st.sidebar:
    st.header("1. Playbook")
    playbook_file = st.file_uploader('Upload playbook (.pdf)', type=['pdf'])
    if playbook_file and st.button('Ingest Playbook'):
        with st.spinner('Embedding and indexing playbook clauses...'):
            files = {'file': (playbook_file.name, playbook_file.getvalue())}
            resp = requests.post(f'{BACKEND_URL}/playbook/ingest', files=files)
        if resp.status_code == 200:
            st.session_state.playbook_ingested = True
            st.success(f'Indexed {resp.json()['chunks_indexed']} playbook chunks.')
        else:
            st.error(f'Ingestion failed: {resp.text}')

    if st.sesion_state.playbook_ingested:
        st.caption('Playbook ready')

# ---- Main: Contract upload + analysis ----
st.header("2. Contract")
contract_file = st.file_uploader('Upload contract (.pdf/.docx)', type=['pdf', 'docx'])

analyze_disabled = not st.session_state.playbook_ingested or contract_file is None
if st.button('Analyze Contract', disabled=analyze_disabled):
    with st.spinner('Segmenting clauses, retrieving playbook context, classifying risk...'):
        files = {'file': (contract_file.name, contract_file.getvalue())}
        resp = requests.post(f"{BACKEND_URL}/contract/analyze", files=files)
    if resp.status_code == 200:
        st.session_state.analysis_result = resp.json()
    else:
        st.error(f'Analysis failed: {resp.text}')

if contract_file is not None and not st.session_state.playbook_ingested:
    st.info('Ingest a playbook first.')

# ---- Output ----
result = st.session_state.analysis_result
if result:
    st.header("3. Negotiation Brief")

    pdf_b64 = result['brief_pdf_base64']
    st.markdown(
        f'<iframe src='data:application/pdf;base64,{pdf_b64}' width='100%' height='600'> </iframe>',
        unsafe_allow_html=True
    )
    st.download_button(
        'Download Brief (PDF)',
        data=base64.b64decode(pdf_b64),
        file_name='negotiation_brief.pdf',
        mime='application/pdf'
    )