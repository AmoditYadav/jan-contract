# D:\jan-contract\agents\demystifier_agent.py

import os
from typing import TypedDict, List
from pydantic import BaseModel, Field

# --- Core LangChain & Document Processing Imports ---
from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser

# LangGraph Imports
from langgraph.graph import StateGraph, END, START

# --- Tool and NEW Core Model Loader Imports ---
from tools.legal_tools import legal_search
from core_utils.core_model_loaders import load_groq_llm, load_embedding_model

# --- 1. Model and Parser Setup ---
# Initialize models by calling the backend-safe loader functions
groq_llm = load_groq_llm()
embedding_model = load_embedding_model()

# --- Pydantic Models (No Changes) ---
class ExplainedTerm(BaseModel):
    term: str = Field(description="The legal term or jargon identified.")
    explanation: str = Field(description="A simple, plain-English explanation of the term.")
    resource_link: str = Field(description="A working URL for a resource explaining this term in India.")

class DemystifyReport(BaseModel):
    summary: str = Field(description="A concise summary of the legal document's purpose and key points.")
    key_terms: List[ExplainedTerm] = Field(description="A list of the most important explained legal terms.")
    overall_advice: str = Field(description="A concluding sentence of general advice.")

# --- 2. LangGraph for Document Analysis (No Changes) ---
class DemystifyState(TypedDict):
    document_chunks: List[str]
    summary: str
    identified_terms: List[str]
    final_report: DemystifyReport

def summarize_node(state: DemystifyState):
    """Takes all document chunks and creates a high-level summary."""
    print("---NODE (Demystify): Generating Summary---")
    context = "\n\n".join(state["document_chunks"])
    prompt = f"You are a paralegal expert... Document Content:\n{context}"
    summary = groq_llm.invoke(prompt).content
    return {"summary": summary}

def identify_terms_node(state: DemystifyState):
    """Identifies the most critical and potentially confusing legal terms in the document."""
    print("---NODE (Demystify): Identifying Key Terms---")
    context = "\n\n".join(state["document_chunks"])
    prompt = f"Based on the following legal document, identify the 3-5 most critical legal terms... Document Content:\n{context}"
    terms_string = groq_llm.invoke(prompt).content
    identified_terms = [term.strip() for term in terms_string.split(',') if term.strip()]
    return {"identified_terms": identified_terms}

def generate_report_node(state: DemystifyState):
    """Combines the summary and terms into a final, structured report with enriched explanations."""
    print("---NODE (Demystify): Generating Final Report---")
    explained_terms_list = []
    document_context = "\n\n".join(state["document_chunks"])
    for term in state["identified_terms"]:
        print(f"  - Researching term: {term}")
        search_results = legal_search.invoke(f"simple explanation of legal term '{term}' in Indian law")
        prompt = f"""A user is reading a legal document that contains the term "{term}".
        Overall document context is: {document_context[:2000]}
        Web search results for "{term}" are: {search_results}
        Format your response strictly as:
        Explanation: [Your simple, one-sentence explanation here]
        URL: [The best, full, working URL from the search results]"""
        response = groq_llm.invoke(prompt).content
        try:
            explanation = response.split("Explanation:")[1].split("URL:")[0].strip()
            link = response.split("URL:")[-1].strip()
        except IndexError:
            explanation = "Could not generate a simple explanation for this term."
            link = "No link found."
        explained_terms_list.append(ExplainedTerm(term=term, explanation=explanation, resource_link=link))
    final_report = DemystifyReport(summary=state["summary"], key_terms=explained_terms_list, overall_advice="This is an automated analysis. For critical matters, please consult with a qualified legal professional.")
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

# --- 3. Helper Function to Create the RAG Chain (No Changes) ---
def create_rag_chain(retriever):
    """Creates the Q&A chain for the interactive chat."""
    prompt_template = """You are a helpful assistant... CONTEXT: {context} QUESTION: {question} ANSWER:"""
    prompt = PromptTemplate.from_template(prompt_template)
    rag_chain = ({"context": retriever, "question": RunnablePassthrough()} | prompt | groq_llm | StrOutputParser())
    return rag_chain

# --- 4. The Master "Controller" Function (No Changes) ---
def process_document_for_demystification(file_path: str):
    """Loads a PDF, runs the full analysis, creates a RAG chain, and returns both."""
    print(f"--- Processing document: {file_path} ---")
    loader = PyMuPDFLoader(file_path)
    documents = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_documents(documents)
    print("--- Creating FAISS vector store for Q&A ---")
    vectorstore = FAISS.from_documents(chunks, embedding=embedding_model)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    rag_chain = create_rag_chain(retriever)
    print("--- Running analysis graph for the report ---")
    chunk_contents = [chunk.page_content for chunk in chunks]
    graph_input = {"document_chunks": chunk_contents}
    result = demystifier_agent_graph.invoke(graph_input)
    report = result.get("final_report")
    return {"report": report, "rag_chain": rag_chain}