# D:\jan-contract\main_streamlit.py

import os
import streamlit as st
from dotenv import load_dotenv

from agents.demystifier_agent import process_document_for_demystification
from components.video_recorder import record_consent_video
from utils.pdf_generator import generate_formatted_pdf

# --- Initial Setup ---
load_dotenv()
st.set_page_config(layout="wide", page_title="Jan-Contract Unified Assistant")
st.title("Jan-Contract: Your Digital Workforce Assistant")

PDF_UPLOAD_DIR = "pdfs_demystify"
os.makedirs(PDF_UPLOAD_DIR, exist_ok=True)

# --- Tabs ---
tab1, tab2, tab3 = st.tabs([
    " **Contract Generator**", 
    " **Scheme Finder**", 
    " **Document Demystifier & Chat**"
])

# --- TAB 1: Contract Generator ---
with tab1:
    st.header("Create a Simple Digital Agreement")
    st.write("Turn your everyday language into a clear agreement, then provide video consent.")
    
    st.subheader("Step 1: Describe and Generate Your Agreement")
    user_request = st.text_area("Describe the agreement...", height=120, key="contract_request")
    
    if st.button("Generate Document & Get Legal Info", type="primary"):
        if user_request:
            with st.spinner("Generating document..."):
                from agents.legal_agent import legal_agent
                result = legal_agent.invoke({"user_request": user_request})
                st.session_state.legal_result = result
                # Reset video state for each new contract
                if 'video_path_from_component' in st.session_state:
                    del st.session_state['video_path_from_component']
                if 'frames_buffer' in st.session_state:
                    del st.session_state['frames_buffer'] # Clear old frames
        else:
            st.error("Please describe the agreement.")
    
    if 'legal_result' in st.session_state:
        result = st.session_state.legal_result
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Generated Digital Agreement")
            st.markdown(result['legal_doc'])
            pdf_bytes = generate_formatted_pdf(result['legal_doc'])
            st.download_button(label="⬇️ Download Formatted PDF", data=pdf_bytes, file_name="agreement.pdf")
        
        with col2:
            st.subheader("Relevant Legal Trivia")
            # ... [Trivia display logic] ...

        st.divider()
        
        st.subheader("Step 2: Record Video Consent for this Agreement")
        saved_video_path = record_consent_video()

        if saved_video_path:
            st.session_state.video_path_from_component = saved_video_path

        if st.session_state.get("video_path_from_component"):
            st.success("✅ Your consent has been recorded and saved!")
            st.video(st.session_state.video_path_from_component)
            st.info("This video is now linked to your generated agreement.")
# --- TAB 2: Scheme Finder (Unchanged) ---
with tab2:
    st.header("Find Relevant Government Schemes")
    st.write("Describe yourself or your situation to find government schemes that might apply to you.")
    
    user_profile = st.text_input("Enter your profile...", key="scheme_profile")
    
    if st.button("Find Schemes", type="primary", key="b2"):
        if user_profile:
            with st.spinner("Initializing models and searching for schemes..."):
                # Lazy import the agent
                from agents.scheme_chatbot import scheme_chatbot
                response = scheme_chatbot.invoke({"user_profile": user_profile})
                st.session_state.scheme_response = response
        else:
            st.error("Please enter a profile.")
            
    if 'scheme_response' in st.session_state:
        response = st.session_state.scheme_response
        st.subheader(f"Potential Schemes for: '{user_profile}'")
        if response and response.schemes:
            for scheme in response.schemes:
                with st.container(border=True):
                    st.markdown(f"#### {scheme.scheme_name}")
                    st.write(f"**Description:** {scheme.description}")
                    st.link_button("Go to Official Page ➡️", scheme.official_link)

# --- TAB 3: Demystifier & Chat (RESTORED to original functionality) ---
with tab3:
    st.header("Simplify & Chat With Your Legal Document")
    st.markdown("Get a plain-English summary of your document, then ask specific follow-up questions.")

    uploaded_file = st.file_uploader("Choose a PDF document", type="pdf", key="demystify_uploader")

    if uploaded_file and st.button("Analyze Document", type="primary"):
        with st.spinner("Performing deep analysis and preparing for chat..."):
            # Save the file to a persistent location
            temp_file_path = os.path.join(PDF_UPLOAD_DIR, uploaded_file.name)
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Single call to the backend agent logic
            analysis_result = process_document_for_demystification(temp_file_path)
            
            # Store the results returned by the agent
            st.session_state.demystify_report = analysis_result["report"]
            st.session_state.rag_chain = analysis_result["rag_chain"]
            st.session_state.messages = [] # Initialize chat history

    # This part of the UI only displays after the analysis is complete
    if 'demystify_report' in st.session_state:
        # Step 1: Display Report
        report = st.session_state.demystify_report
        st.divider()
        st.header("Step 1: Automated Document Analysis")
        with st.container(border=True):
            st.subheader("📄 Document Summary")
            st.write(report.summary)
            st.divider()
            st.subheader("🔑 Key Terms Explained")
            for term in report.key_terms:
                with st.expander(f"**{term.term}**"):
                    st.write(term.explanation)
                    st.markdown(f"[Learn More Here]({term.resource_link})")
            st.divider()
            st.success(f"**Overall Advice:** {report.overall_advice}")
        st.divider()

        # Step 2: Display Chat
        st.header("Step 2: Ask Follow-up Questions")
        st.info("The document is now ready for your questions. Chat with it below.")

        for message in st.session_state.get("messages", []):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Ask a specific question about the document..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Searching the document..."):
                    rag_chain = st.session_state.rag_chain
                    response = rag_chain.invoke(prompt)
                    st.markdown(response)
            
            st.session_state.messages.append({"role": "assistant", "content": response})

    elif not uploaded_file:
        st.info("Upload a PDF document to begin the analysis.")