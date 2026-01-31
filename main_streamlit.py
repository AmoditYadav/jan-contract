# D:\jan-contract\main_streamlit.py

import os
import streamlit as st
import requests
from dotenv import load_dotenv

# --- 1. Initial Setup ---
load_dotenv()
st.set_page_config(layout="wide", page_title="Jan-Contract Unified Assistant", page_icon="⚖️")

# Backend Configuration
# In production (Streamlit Cloud), set BACKEND_URL in secrets or env vars
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# Only strip trailing slash if it exists, to avoid removing the last char of a valid URL if logic differs
if BACKEND_URL.endswith("/"):
    BACKEND_URL = BACKEND_URL[:-1]

# --- Custom CSS ---
st.markdown("""
<style>
    .main-header { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #333; }
    h1 { color: #1A73E8; }
    h2, h3 { color: #424242; }
    .stButton>button { color: #ffffff; background-color: #1A73E8; border-radius: 5px; }
    .success-msg { color: #2e7d32; font-weight: bold; }
    .error-msg { color: #c62828; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("Jan-Contract: Digital Workforce Assistant")
st.caption(f"Connected to Backend: `{BACKEND_URL}`")
st.write("Empowering India's workforce with accessible legal tools and government scheme discovery.")

# --- 2. Streamlit UI with Tabs ---
tab1, tab2, tab3 = st.tabs([
    "Contract Generator", 
    "Scheme Finder", 
    "Document Demystifier"
])

# --- TAB 1: Contract Generator ---
with tab1:
    st.header("Digital Agreement Generator")
    st.write("Create a clear digital agreement from plain text and record video consent.")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Agreement Details")
        user_request = st.text_area("Describe the terms of the agreement...", height=150, key="contract_request", placeholder="E.g., I, Rajesh, agree to paint Mr. Sharma's house for 5000 rupees by next Tuesday.")
        
        if st.button("Generate Agreement", type="primary", key="btn_generate_contract"):
            if user_request:
                with st.spinner("Drafting agreement via API..."):
                    try:
                        payload = {"user_request": user_request}
                        response = requests.post(f"{BACKEND_URL}/api/v1/contracts/generate", json=payload)
                        
                        if response.status_code == 200:
                            data = response.json()
                            if data.get("success"):
                                st.session_state.legal_result = data["data"]
                                if 'video_path_from_component' in st.session_state:
                                    del st.session_state['video_path_from_component']
                            else:
                                st.error(f"API Error: {data.get('message')}")
                        else:
                            st.error(f"Server Error: {response.text}")
                    except Exception as e:
                        st.error(f"Connection failed: {e}")
            else:
                st.warning("Please describe the agreement details.")
    
    with col2:
        if 'legal_result' in st.session_state:
            result = st.session_state.legal_result
            contract_text = result.get('contract', '')
            
            st.subheader("Drafted Agreement")
            with st.container(border=True):
                st.markdown(contract_text)
            
            # PDF Download via API
            if st.button("Download PDF"):
                 try:
                    pdf_Payload = {"user_request": result.get('user_request', user_request)}
                    pdf_resp = requests.post(f"{BACKEND_URL}/api/v1/contracts/generate-pdf", json=pdf_Payload)
                    if pdf_resp.status_code == 200:
                        st.download_button(label="Click to Save PDF", data=pdf_resp.content, file_name="agreement.pdf", mime="application/pdf")
                    else:
                        st.error("Failed to generate PDF")
                 except Exception as e:
                     st.error(f"Download failed: {e}")

            if result.get('legal_trivia') and result['legal_trivia'].get('trivia'):
                with st.expander("Legal Insights"):
                    for item in result['legal_trivia']['trivia']:
                        st.markdown(f"**{item['point']}**")
                        st.caption(item['explanation'])
                        st.markdown(f"[Source]({item['source_url']})")

    st.divider()
    from components.video_recorder import record_consent_video
    st.subheader("Video Consent Recording")
    saved_video_path = record_consent_video()
    
    # Upload video to backend if recorded
    if saved_video_path and 'legal_result' in st.session_state:
        contract_id = st.session_state.legal_result.get('contract_id')
        if contract_id:
             if st.button("Upload Consent to Server"):
                try:
                    with open(saved_video_path, 'rb') as f:
                        files = {'file': (os.path.basename(saved_video_path), f, 'video/mp4')}
                        data = {'contract_id': contract_id, 'consent_text': "I agree to the terms."}
                        up_resp = requests.post(f"{BACKEND_URL}/api/v1/media/upload-video", files=files, data=data)
                        if up_resp.status_code == 200:
                            st.success("Consent uploaded to server securely!")
                        else:
                            st.error(f"Upload failed: {up_resp.text}")
                except Exception as e:
                    st.error(f"Upload error: {e}")

# --- TAB 2: Scheme Finder ---
with tab2:
    st.header("Government Scheme Finder")
    st.write("Find relevant government schemes based on your profile.")
    
    user_profile = st.text_input("Enter your profile description...", key="scheme_profile", placeholder="E.g., A female farmer in Maharashtra owning 2 acres of land.")
    
    if st.button("Search Schemes", type="primary", key="btn_find_schemes"):
        if user_profile:
            with st.spinner("Searching schemes via API..."):
                try:
                    payload = {"user_profile": user_profile}
                    response = requests.post(f"{BACKEND_URL}/api/v1/schemes/find", json=payload)
                    
                    if response.status_code == 200:
                        st.session_state.scheme_response = response.json().get('data', {})
                    else:
                        st.error(f"Error: {response.text}")
                except Exception as e:
                    st.error(f"Connection error: {e}")
        else:
            st.warning("Please enter a profile description.")
            
    if 'scheme_response' in st.session_state:
        response = st.session_state.scheme_response
        st.subheader(f"Results")
        schemes = response.get('schemes', [])
        if schemes:
            for scheme in schemes:
                with st.container(border=True):
                    st.markdown(f"#### {scheme.get('scheme_name')}")
                    st.write(scheme.get('description'))
                    st.write(f"**Target Audience:** {scheme.get('target_audience')}")
                    st.markdown(f"[Official Website]({scheme.get('official_link')})")
        else:
            st.info("No specific schemes found.")

# --- TAB 3: Demystifier ---
with tab3:
    st.header("Document Demystifier")
    st.write("Upload a legal document to get a simplified summary and ask questions.")

    uploaded_file = st.file_uploader("Upload PDF Document", type="pdf", key="demystify_uploader")

    if uploaded_file and st.button("Analyze Document", type="primary"):
        with st.spinner("Uploading and analyzing..."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                response = requests.post(f"{BACKEND_URL}/api/v1/demystify/upload", files=files)
                
                if response.status_code == 200:
                    st.session_state.demystify_data = response.json().get('data', {})
                    st.session_state.session_id = st.session_state.demystify_data.get('session_id')
                    st.success("Analysis complete!")
                else:
                    st.error(f"Analysis failed: {response.text}")
            except Exception as e:
                st.error(f"Connection error: {e}")

    if 'demystify_data' in st.session_state:
        st.divider()
        report = st.session_state.demystify_data.get('report', {})
        
        tab_summary, tab_chat = st.tabs(["Summary & Analysis", "Chat with Document"])
        
        with tab_summary:
            st.subheader("Document Summary")
            st.write(report.get('summary', ''))
            
            st.subheader("Key Terms Explained")
            for term in report.get('key_terms', []):
                with st.expander(f"{term.get('term')}"):
                    st.write(term.get('explanation'))
                    st.markdown(f"[Learn More]({term.get('resource_link')})")
            
            st.info(f"**Advice:** {report.get('overall_advice')}")
        
        with tab_chat:
            st.subheader("Ask Questions")
            
            # Simple Chat Interface for API
            if "messages" not in st.session_state:
                st.session_state.messages = []

            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            if prompt := st.chat_input("Ask about the document..."):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        try:
                            payload = {
                                "session_id": st.session_state.session_id,
                                "question": prompt
                            }
                            chat_resp = requests.post(f"{BACKEND_URL}/api/v1/demystify/chat", json=payload)
                            if chat_resp.status_code == 200:
                                answer = chat_resp.json()['data']['answer']
                                st.markdown(answer)
                                st.session_state.messages.append({"role": "assistant", "content": answer})
                            else:
                                st.error("Failed to get answer.")
                        except Exception as e:
                            st.error(f"Error: {e}")


# --- 1. Initial Setup ---
load_dotenv()
st.set_page_config(layout="wide", page_title="Jan-Contract Unified Assistant", page_icon="⚖️")

# Custom CSS for a cleaner look
st.markdown("""
<style>
    .reportview-container {
        background: #f0f2f6;
    }
    .main-header {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        color: #333;
    }
    h1 {
        color: #1A73E8;
    }
    h2, h3 {
        color: #424242;
    }
    .stButton>button {
        color: #ffffff;
        background-color: #1A73E8;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

st.title("Jan-Contract: Digital Workforce Assistant")
st.write("Empowering India's workforce with accessible legal tools and government scheme discovery.")

PDF_UPLOAD_DIR = "pdfs_demystify"
os.makedirs(PDF_UPLOAD_DIR, exist_ok=True)

# --- 2. Streamlit UI with Tabs ---
tab1, tab2, tab3 = st.tabs([
    "Contract Generator", 
    "Scheme Finder", 
    "Document Demystifier"
])

# --- TAB 1: Contract Generator ---
with tab1:
    st.header("Digital Agreement Generator")
    st.write("Create a clear digital agreement from plain text and record video consent.")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Agreement Details")
        user_request = st.text_area("Describe the terms of the agreement...", height=150, key="contract_request", placeholder="E.g., I, Rajesh, agree to paint Mr. Sharma's house for 5000 rupees by next Tuesday.")
        
        if st.button("Generate Agreement", type="primary", key="btn_generate_contract"):
            if user_request:
                with st.spinner("Drafting agreement..."):
                    try:
                        from agents.legal_agent import legal_agent
                        result = legal_agent.invoke({"user_request": user_request})
                        st.session_state.legal_result = result
                        # Reset video state for new contract
                        if 'video_path_from_component' in st.session_state:
                            del st.session_state['video_path_from_component']
                    except Exception as e:
                        st.error(f"An error occurred: {e}")
            else:
                st.warning("Please describe the agreement details.")
    
    with col2:
        if 'legal_result' in st.session_state:
            result = st.session_state.legal_result
            
            st.subheader("Drafted Agreement")
            with st.container(border=True):
                st.markdown(result['legal_doc'])
            
            pdf_bytes = generate_formatted_pdf(result['legal_doc'])
            st.download_button(label="Download PDF", data=pdf_bytes, file_name="agreement.pdf", mime="application/pdf")
            
            if result.get('legal_trivia') and result['legal_trivia'].trivia:
                with st.expander("Legal Insights"):
                    for item in result['legal_trivia'].trivia:
                        st.markdown(f"**{item.point}**")
                        st.caption(item.explanation)
                        st.markdown(f"[Source]({item.source_url})")

    st.divider()
    
    st.subheader("Video Consent Recording")
    st.info("Please record a video stating your name and that you agree to the terms above.")
    
    saved_video_path = record_consent_video()

    if saved_video_path:
        st.session_state.video_path_from_component = saved_video_path

    if st.session_state.get("video_path_from_component"):
        st.success("Consent recorded successfully.")
        st.video(st.session_state.video_path_from_component)

# --- TAB 2: Scheme Finder ---
with tab2:
    st.header("Government Scheme Finder")
    st.write("Find relevant government schemes based on your profile.")
    
    user_profile = st.text_input("Enter your profile description...", key="scheme_profile", placeholder="E.g., A female farmer in Maharashtra owning 2 acres of land.")
    
    if st.button("Search Schemes", type="primary", key="btn_find_schemes"):
        if user_profile:
            with st.spinner("Searching for schemes..."):
                try:
                    from agents.scheme_chatbot import scheme_chatbot
                    response = scheme_chatbot.invoke({"user_profile": user_profile})
                    st.session_state.scheme_response = response
                except Exception as e:
                    st.error(f"An error occurred during search: {e}")
        else:
            st.warning("Please enter a profile description.")
            
    if 'scheme_response' in st.session_state:
        response = st.session_state.scheme_response
        st.subheader(f"Schemes for: '{user_profile}'")
        if response and response.schemes:
            for scheme in response.schemes:
                with st.container(border=True):
                    st.markdown(f"#### {scheme.scheme_name}")
                    st.write(scheme.description)
                    st.write(f"**Target Audience:** {scheme.target_audience}")
                    st.markdown(f"[Official Website]({scheme.official_link})")
        else:
            st.info("No specific schemes found. Try a more detailed description.")

# --- TAB 3: Demystifier & Chat ---
with tab3:
    st.header("Document Demystifier")
    st.write("Upload a legal document to get a simplified summary and ask questions.")

    uploaded_file = st.file_uploader("Upload PDF Document", type="pdf", key="demystify_uploader")

    if uploaded_file and st.button("Analyze Document", type="primary"):
        with st.spinner("Analyzing document..."):
            try:
                temp_file_path = os.path.join(PDF_UPLOAD_DIR, uploaded_file.name)
                with open(temp_file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                analysis_result = process_document_for_demystification(temp_file_path)
                
                st.session_state.demystifier_report = analysis_result["report"]
                st.session_state.rag_chain = analysis_result["rag_chain"]
            except Exception as e:
                st.error(f"Analysis failed: {e}")

    if 'demystifier_report' in st.session_state:
        st.divider()
        report = st.session_state.demystifier_report
        
        tab_summary, tab_chat = st.tabs(["Summary & Analysis", "Chat with Document"])
        
        with tab_summary:
            st.subheader("Document Summary")
            st.write(report.summary)
            
            st.subheader("Key Terms Explained")
            for term in report.key_terms:
                with st.expander(f"{term.term}"):
                    st.write(term.explanation)
                    st.markdown(f"[Learn More]({term.resource_link})")
            
            st.info(f"**Advice:** {report.overall_advice}")
        
        with tab_chat:
            st.subheader("Ask Questions")
            chat_interface(
                handler_function=st.session_state.rag_chain.invoke, 
                session_state_key="doc_chat_history"
            )


