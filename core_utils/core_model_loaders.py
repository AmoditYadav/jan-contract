# D:\jan-contract\core_utils\core_model_loaders.py

import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings

def load_embedding_model():
    """Loads the embedding model without any Streamlit dependencies or heavy local models."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("CRITICAL WARNING: GOOGLE_API_KEY is missing. Embeddings will fail.")
        from langchain_core.runnables import RunnableLambda
        def fail_on_invoke(input):
            raise ValueError("GOOGLE_API_KEY is missing. Please check your environment variables.")
        return RunnableLambda(fail_on_invoke)

    return GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=api_key)

def load_groq_llm():
    """Loads the Groq LLM without any Streamlit dependencies."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("CRITICAL WARNING: GROQ_API_KEY is missing. Scheme finder will fail.")
        from langchain_core.runnables import RunnableLambda
        def fail_on_invoke(input):
            raise ValueError("GROQ_API_KEY is missing. Please check your environment variables.")
        return RunnableLambda(fail_on_invoke)
        
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
        from langchain_core.runnables import RunnableLambda
        def fail_on_invoke(input):
            raise ValueError("GOOGLE_API_KEY is missing. Please check your environment variables.")
        return RunnableLambda(fail_on_invoke)
        
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        temperature=0, 
        max_retries=5,
        google_api_key=api_key
    )