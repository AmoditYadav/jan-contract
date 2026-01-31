# D:\jan-contract\agents\demystifier_agent.py

import os
from typing import TypedDict, List
from pydantic import BaseModel, Field

# --- Core LangChain & Document Processing Imports ---
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# LangGraph Imports
from langgraph.graph import StateGraph, END, START

# --- Tool and Core Model Loader Imports ---
from tools.legal_tools import legal_search
from core_utils.core_model_loaders import load_groq_llm, load_embedding_model

# --- 1. Model and Parser Setup ---
# Initialize models by calling the backend-safe loader functions
groq_llm = load_groq_llm()
embedding_model = load_embedding_model()

# --- Pydantic Models ---
class ExplainedTerm(BaseModel):
    term: str = Field(description="The legal term or jargon identified.")
    explanation: str = Field(description="A simple, plain-English explanation of the term.")
    resource_link: str = Field(description="A working URL for a resource explaining this term in India.")

class DemystifyReport(BaseModel):
    summary: str = Field(description="A concise summary of the legal document's purpose and key points.")
    key_terms: List[ExplainedTerm] = Field(description="A list of the most important explained legal terms.")
    overall_advice: str = Field(description="A concluding sentence of general advice.")

# --- 2. LangGraph for Document Analysis ---
class DemystifyState(TypedDict):
    document_chunks: List[str]
    summary: str
    identified_terms: List[str]
    final_report: DemystifyReport

def summarize_node(state: DemystifyState):
    """Takes all document chunks and creates a high-level summary."""
    print("---NODE (Demystify): Generating Summary---")
    chunks = state.get("document_chunks", [])
    if not chunks:
        return {"summary": "No content to summarize."}
        
    context = "\n\n".join(chunks)
    prompt = f"You are a paralegal expert for the Indian legal system. Summarize the following document clearly for a layman:\n\n{context}"
    try:
        response = groq_llm.invoke(prompt)
        summary = response.content if response and response.content else "Summary generation failed."
    except Exception as e:
        print(f"Summary generation error: {e}")
        summary = "Summary generation failed due to an error."
        
    return {"summary": summary}

def identify_terms_node(state: DemystifyState):
    """Identifies the most critical and potentially confusing legal terms in the document."""
    print("---NODE (Demystify): Identifying Key Terms---")
    try:
        context = "\n\n".join(state.get("document_chunks", []))
        if not context:
            print("Warning: No document context found for term identification.")
            return {"identified_terms": []}
            
        prompt = f"Identify the 3-5 most critical complex legal terms in the following document that a layman would not understand. Return only the terms separated by commas.\n\n{context}"
        response = groq_llm.invoke(prompt)
        
        if not response or not response.content:
            print("Warning: Empty response from LLM for term identification.")
            return {"identified_terms": []}
            
        terms_string = response.content
        identified_terms = [term.strip() for term in terms_string.split(',') if term.strip()]
        return {"identified_terms": identified_terms}
    except Exception as e:
        print(f"Error in identify_terms_node: {e}")
        return {"identified_terms": []}

def generate_report_node(state: DemystifyState):
    """Combines the summary and terms into a final, structured report with enriched explanations."""
    print("---NODE (Demystify): Generating Final Report---")
    explained_terms_list = []
    
    # Handle None or empty document_chunks
    chunks = state.get("document_chunks", [])
    document_context = "\n\n".join(chunks) if chunks else ""
    
    # Handle None identified_terms
    terms = state.get("identified_terms", [])
    if terms is None:
        terms = []
        
    for term in terms:
        print(f"  - Researching term: {term}")
        try:
            search_results = legal_search.invoke(f"simple explanation of legal term '{term}' in Indian law")
        except Exception as e:
            print(f"Search failed for term '{term}': {e}")
            search_results = "Search unavailable."

        prompt = f"""
        A user is reading a legal document containing the term "{term}".
        Context: {document_context[:2000]}...
        Search Results: {search_results}
        
        Provide a simple one-sentence explanation and a valid URL if found.
        Format:
        Explanation: [Explanation]
        URL: [URL]
        """
        try:
            response = groq_llm.invoke(prompt)
            if response and response.content:
                content = response.content
                try:
                    if "Explanation:" in content and "URL:" in content:
                        explanation = content.split("Explanation:")[1].split("URL:")[0].strip()
                        link = content.split("URL:")[-1].strip()
                    else:
                        explanation = content.strip()
                        link = "https://kanoon.nearlaw.com/"
                except Exception:
                    explanation = f"Legal term '{term}' identified."
                    link = "https://kanoon.nearlaw.com/"
            else:
                 explanation = "Explanation unavailable."
                 link = "https://kanoon.nearlaw.com/"
        except Exception as e:
            print(f"LLM failed for term '{term}': {e}")
            explanation = "Explanation unavailable."
            link = "https://kanoon.nearlaw.com/"
            
        explained_terms_list.append(ExplainedTerm(term=term, explanation=explanation, resource_link=link))
        
    # Ensure summary is not None
    summary_text = state.get("summary", "Summary unavailable.")
    if summary_text is None:
        summary_text = "Summary unavailable."

    final_report = DemystifyReport(
        summary=summary_text, 
        key_terms=explained_terms_list, 
        overall_advice="This AI analysis is for informational purposes only. Consult a lawyer for binding advice."
    )
    return {"final_report": final_report}

# Compile the analysis graph
graph_builder = StateGraph(DemystifyState)
graph_builder.add_node("summarize", summarize_node)
graph_builder.add_node("identify_terms", identify_terms_node)
graph_builder.add_node("generate_report", generate_report_node)
graph_builder.add_edge(START, "summarize")
graph_builder.add_edge("summarize", "identify_terms")
graph_builder.add_edge("identify_terms", "generate_report")
graph_builder.add_edge("generate_report", END)
demystifier_agent_graph = graph_builder.compile()

# --- 3. Helper Function to Create the RAG Chain ---
def create_rag_chain(retriever):
    """Creates the Q&A chain for the interactive chat."""
    prompt_template = """You are a helpful legal assistant. Answer based on the context only.
    CONTEXT: {context} 
    QUESTION: {question} 
    ANSWER:"""
    prompt = PromptTemplate.from_template(prompt_template)
    rag_chain = ({"context": retriever, "question": RunnablePassthrough()} | prompt | groq_llm | StrOutputParser())
    return rag_chain

# --- 4. The Master "Controller" Function ---
def process_document_for_demystification(file_path: str):
    """Loads a PDF, runs the full analysis, creates a RAG chain, and returns both."""
    print(f"--- Processing document: {file_path} ---")
    
    loader = PyMuPDFLoader(file_path)
    documents = loader.load()
    
    if not documents:
        raise ValueError("No content found in PDF.")

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_documents(documents)
    
    print("--- Creating FAISS vector store for Q&A ---")
    vectorstore = FAISS.from_documents(chunks, embedding=embedding_model)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    rag_chain = create_rag_chain(retriever)
    
    print("--- Running analysis graph for the report ---")
    chunk_contents = [chunk.page_content for chunk in chunks]
    # Limit context to avoid token limits if document is huge
    graph_input = {"document_chunks": chunk_contents[:10]} 
    
    result = demystifier_agent_graph.invoke(graph_input)
    report = result.get("final_report")
    
    return {"report": report, "rag_chain": rag_chain}