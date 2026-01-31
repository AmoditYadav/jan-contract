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
    return ChatGroq(temperature=0, model="meta-llama/llama-4-scout-17b-16e-instruct", api_key=os.getenv("GROQ_API_KEY"))

def load_gemini_llm():
    """Loads the Gemini LLM without any Streamlit dependencies."""
    return ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0, max_retries=5)