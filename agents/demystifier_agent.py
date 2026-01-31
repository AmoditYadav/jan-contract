# D:\jan-contract\agents\demystifier_agent.py

import os
from typing import TypedDict, List
from pydantic import BaseModel, Field

# --- Core LangChain & Document Processing Imports ---
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from core_utils.simple_vectorstore import SimpleVectorStore
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# ... (rest of imports)

# ...

# --- 4. The Master "Controller" Function ---
def process_document_for_demystification(file_path: str):
    """Loads a PDF, runs the full analysis, creates a RAG chain, and returns both."""
    print(f"--- Processing document: {file_path} ---")
    
    loader = PyPDFLoader(file_path)
    documents = loader.load()
    
    if not documents:
        raise ValueError("No content found in PDF.")

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_documents(documents)
    
    print("--- Creating Simple vector store (NumPy) for Q&A ---")
    vectorstore = SimpleVectorStore.from_documents(chunks, embedding=embedding_model)
    # SimpleVectorStore doesn't support as_retriever directly in the same way as FAISS without modification, 
    # but we can wrap it or just use it as a retriever if we implemented as_retriever.
    # Actually, VectorStore base class has as_retriever.
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    rag_chain = create_rag_chain(retriever)
    
    print("--- Running analysis graph for the report ---")
    chunk_contents = [chunk.page_content for chunk in chunks]
    # Limit context to avoid token limits if document is huge
    graph_input = {"document_chunks": chunk_contents[:10]} 
    
    result = demystifier_agent_graph.invoke(graph_input)
    report = result.get("final_report")
    
    return {"report": report, "rag_chain": rag_chain}