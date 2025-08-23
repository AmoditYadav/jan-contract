# D:\jan-contract\utils\model_loaders.py

import streamlit as st
# Import from our new backend-safe loader
from core_utils.core_model_loaders import load_embedding_model, load_groq_llm, load_gemini_llm

@st.cache_resource
def get_embedding_model():
    """Loads and caches the embedding model for the Streamlit app."""
    with st.spinner("Initializing embedding model (this is a one-time download)..."):
        model = load_embedding_model()
    return model

@st.cache_resource
def get_groq_llm():
    """Loads and caches the Groq LLM for the Streamlit app."""
    return load_groq_llm()

@st.cache_resource
def get_gemini_llm():
    """Loads and caches the Gemini LLM for the Streamlit app."""
    return load_gemini_llm()