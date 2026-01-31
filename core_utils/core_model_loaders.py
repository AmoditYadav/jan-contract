# D:\jan-contract\core_utils\core_model_loaders.py

import os
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI

# --- Simple, non-caching functions for the backend ---
# These can be safely imported by FastAPI or any other backend script.

def load_embedding_model():
    """Loads the embedding model without any Streamlit dependencies."""
    return FastEmbedEmbeddings(model_name="BAAI/bge-base-en-v1.5")

def load_groq_llm():
    """Loads the Groq LLM without any Streamlit dependencies."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("CRITICAL WARNING: GROQ_API_KEY is missing. Scheme finder will fail.")
        class DummyLLM:
            def invoke(self, *args, **kwargs):
                raise ValueError("GROQ_API_KEY is missing. Please check your environment variables.")
        return DummyLLM()
        
    return ChatGroq(
        temperature=0, 
        model="meta-llama/llama-3.3-70b-versatile", # Switched to a standard stable model
        api_key=api_key
    )

def load_gemini_llm():
    """Loads the Gemini LLM without any Streamlit dependencies."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("CRITICAL WARNING: GOOGLE_API_KEY is missing. AI features will fail.")
        # Return a dummy callable that fails gracefully at runtime, not logic load time
        class DummyLLM:
            def invoke(self, *args, **kwargs):
                raise ValueError("GOOGLE_API_KEY is missing. Please check your environment variables.")
        return DummyLLM()
        
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        temperature=0, 
        max_retries=5,
        google_api_key=api_key
    )