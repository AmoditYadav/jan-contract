# D:\jan-contract\agents\legal_agent.py

import os
from langchain.prompts import PromptTemplate
from langgraph.graph import StateGraph, END
from typing import List, TypedDict
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser

# --- Tool and NEW Core Model Loader Imports ---
from tools.legal_tools import legal_search
from core_utils.core_model_loaders import load_gemini_llm

# --- Pydantic Models (No Changes) ---
class LegalTriviaItem(BaseModel):
    point: str = Field(description="A concise summary of the legal point or right.")
    explanation: str = Field(description="A brief explanation of what the point means for the user.")
    source_url: str = Field(description="The full, working URL to the official source or a highly reputable article explaining the law.")

class LegalTriviaOutput(BaseModel):
    trivia: List[LegalTriviaItem] = Field(description="A list of structured legal trivia items.")

# --- Setup Models and Parsers ---
parser = PydanticOutputParser(pydantic_object=LegalTriviaOutput)

# --- Initialize the LLM by calling the backend-safe loader function ---
llm = load_gemini_llm()

# --- LangGraph State (No Changes) ---
class LegalAgentState(TypedDict):
    user_request: str
    legal_doc: str
    legal_trivia: LegalTriviaOutput

# --- LangGraph Nodes (No Changes) ---
def generate_legal_doc(state: LegalAgentState):
    prompt_text = f"Based on the user's request, generate a simple legal document text for an informal agreement in India. Keep it clear and simple.\n\nUser Request: {state['user_request']}"
    legal_doc_text = llm.invoke(prompt_text).content
    return {"legal_doc": legal_doc_text}

def get_legal_trivia(state: LegalAgentState):
    prompt = PromptTemplate(
        template="""
        You are a specialized legal assistant for India's informal workforce...
        User's situation: {user_request}
        Web search results: {search_results}
        {format_instructions}
        """,
        input_variables=["user_request", "search_results"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    chain = prompt | llm | parser
    search_results = legal_search.invoke(state["user_request"])
    structured_trivia = chain.invoke({"user_request": state["user_request"], "search_results": search_results})
    return {"legal_trivia": structured_trivia}

# --- Build Graph (No Changes) ---
workflow = StateGraph(LegalAgentState)
workflow.add_node("generate_legal_doc", generate_legal_doc)
workflow.add_node("get_legal_trivia", get_legal_trivia)
workflow.set_entry_point("generate_legal_doc")
workflow.add_edge("generate_legal_doc", "get_legal_trivia")
workflow.add_edge("get_legal_trivia", END)
legal_agent = workflow.compile()