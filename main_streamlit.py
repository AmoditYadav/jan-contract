# D:\jan-contract\main_streamlit.py

import os
import streamlit as st
from dotenv import load_dotenv

# --- Agent and Component Imports (Cleaned up) ---
from agents.demystifier_agent import process_document_for_demystification
from components.video_recorder import record_consent_video
from utils.pdf_generator import generate_formatted_pdf
from components.chat_interface import chat_interface
from agents.general_assistant_agent import ask_gemini
# --- 1. Initial Setup ---
load_dotenv()
st.set_page_config(layout="wide", page_title="Jan-Contract Unified Assistant")
st.title("Jan-Contract: Your Digital Workforce Assistant")

PDF_UPLOAD_DIR = "pdfs_demystify"
os.makedirs(PDF_UPLOAD_DIR, exist_ok=True)

# --- 2. Streamlit UI with Tabs ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📝 **Contract Generator**", 
    "🏦 **Scheme Finder**", 
    "📜 **Document Demystifier & Chat**",
    "🤖 **General Assistant**"
])

# --- TAB 1: Contract Generator ---
with tab1:
    st.header("Create a Simple Digital Agreement")
    st.write("Turn your everyday language into a clear agreement, then provide video consent.")
    
    st.subheader("Step 1: Describe and Generate Your Agreement")
    user_request = st.text_area("Describe the agreement...", height=120, key="contract_request")
    
    # --- FIX: Added a unique key="b1" for consistency ---
    if st.button("Generate Document & Get Legal Info", type="primary", key="b1"):
        if user_request:
            with st.spinner("Generating document..."):
                from agents.legal_agent import legal_agent
                result = legal_agent.invoke({"user_request": user_request})
                st.session_state.legal_result = result
                # Reset video state for each new contract
                if 'video_path_from_component' in st.session_state:
                    del st.session_state['video_path_from_component']
                if 'frames_buffer' in st.session_state:
                    del st.session_state['frames_buffer']
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
            # --- FIX: Restored the missing trivia display logic ---
            if result.get('legal_trivia') and result['legal_trivia'].trivia:
                for item in result['legal_trivia'].trivia:
                    st.markdown(f"- **{item.point}**")
                    st.caption(item.explanation)
                    st.markdown(f"[Source Link]({item.source_url})")
            else:
                st.write("Could not retrieve structured legal trivia.")

        st.divider()
        
        st.subheader("Step 2: Record Video Consent for this Agreement")
        
        # Browser compatibility check
        st.info("🌐 **Browser Requirements:** This feature works best in Chrome, Firefox, or Edge. Make sure to allow camera access when prompted.")
        
        saved_video_path = record_consent_video()

        if saved_video_path:
            st.session_state.video_path_from_component = saved_video_path

        if st.session_state.get("video_path_from_component"):
            st.success("✅ Your consent has been recorded and saved!")
            st.video(st.session_state.video_path_from_component)
            st.info("This video is now linked to your generated agreement.")
        else:
            st.info("💡 **Tip:** If video recording isn't working, try refreshing the page and allowing camera permissions.")

# --- TAB 2: Scheme Finder (Unchanged) ---
with tab2:
    st.header("Find Relevant Government Schemes")
    st.write("Describe yourself or your situation to find government schemes that might apply to you.")
    
    user_profile = st.text_input("Enter your profile...", key="scheme_profile")
    
    if st.button("Find Schemes", type="primary", key="b2"):
        if user_profile:
            with st.spinner("Initializing models and searching for schemes..."):
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

# --- TAB 3: Demystifier & Chat ---
with tab3:
    st.header("📜 Simplify & Chat With Your Legal Document")
    st.markdown("Get a plain-English summary of your document, then ask questions using text or your voice.")

    uploaded_file = st.file_uploader("Choose a PDF document", type="pdf", key="demystify_uploader")

    # This button triggers the one-time analysis and embedding process
    if uploaded_file and st.button("Analyze Document", type="primary"):
        with st.spinner("Performing deep analysis and preparing for chat..."):
            # Save the uploaded file to a temporary location for processing
            temp_file_path = os.path.join(PDF_UPLOAD_DIR, uploaded_file.name)
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Call the master controller function from the agent
            analysis_result = process_document_for_demystification(temp_file_path)
            
            # Store the two key results in the session state
            st.session_state.demystifier_report = analysis_result["report"]
            st.session_state.rag_chain = analysis_result["rag_chain"]

    # This UI section only appears after a document has been successfully analyzed
    if 'demystifier_report' in st.session_state:
        st.divider()
        st.header("Step 1: Automated Document Analysis")
        report = st.session_state.demystifier_report
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

        st.header("Step 2: Ask Follow-up Questions")
        # Call our reusable chat component, passing the RAG chain specific to this document.
        # The RAG chain's .invoke method is the handler function.
        chat_interface(
            handler_function=st.session_state.rag_chain.invoke, 
            session_state_key="doc_chat_history"  # Use a unique key for this chat's history
        )
            
    elif not uploaded_file:
        st.info("Upload a PDF document to begin analysis and enable chat.")

# --- TAB 4: General Assistant (Complete) ---
with tab4:
    st.header("🤖 General Assistant")
    st.markdown("Ask a general question and get a response directly from the Gemini AI model. You can use text or your voice.")

    # Call our reusable chat component.
    # This time, we pass the simple `ask_gemini` function as the handler.
    chat_interface(
        handler_function=ask_gemini,
        session_state_key="general_chat_history" # Use a different key for this chat's history
    )