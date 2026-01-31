# D:\jan-contract\agents\legal_agent.py

import os
from langchain_core.prompts import PromptTemplate
from langgraph.graph import StateGraph, END
from typing import List, TypedDict, Optional
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser

# --- Tool and Core Model Loader Imports ---
from tools.legal_tools import legal_search
from core_utils.core_model_loaders import load_gemini_llm

# --- Pydantic Models ---
class LegalTriviaItem(BaseModel):
    point: str = Field(description="A concise summary of the legal point or right.")
    explanation: str = Field(description="A brief explanation of what the point means for the user.")
    source_url: str = Field(description="The full, working URL to the official source or a highly reputable article explaining the law.")

class LegalTriviaOutput(BaseModel):
    trivia: List[LegalTriviaItem] = Field(description="A list of structured legal trivia items.")

# --- Setup Models and Parsers ---
parser = PydanticOutputParser(pydantic_object=LegalTriviaOutput)

# --- Initialize the LLM ---
llm = load_gemini_llm()

# --- LangGraph State ---
class LegalAgentState(TypedDict):
    user_request: str
    legal_doc: str
    legal_trivia: Optional[LegalTriviaOutput]

# --- LangGraph Nodes ---
def generate_legal_doc(state: LegalAgentState):
    """Generates the legal document based on user request."""
    print("---NODE: Generating Legal Document---")
    prompt_text = (
        f"You are a professional legal drafter for the Indian context. "
        f"Create a simple, clear, and legally valid digital agreement based on the request below. "
        f"Do not use emojis. Use professional formatting (Markdown). "
        f"Focus on clarity for informal workers.\n\n"
        f"User Request: {state['user_request']}"
    )
    try:
        response = llm.invoke(prompt_text)
        legal_doc_text = response.content if response and response.content else "Error: Failed to generate contract."
    except Exception as e:
        print(f"Contract generation error: {e}")
        legal_doc_text = "Error: Failed to generate contract due to an internal error."
        
    return {"legal_doc": legal_doc_text}

def get_legal_trivia(state: LegalAgentState):
    """Fetches relevant legal trivia to educate the user."""
    print("---NODE: Fetching Legal Trivia---")
    prompt = PromptTemplate(
        template="""
        You are a specialized legal assistant for India's workforce.
        Based on the user's situation, provide 3 important legal rights or points they should be aware of.
        
        User's situation: {user_request}
        Web search results: {search_results}
        
        {format_instructions}
        """,
        input_variables=["user_request", "search_results"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    chain = prompt | llm | parser
    
    try:
        search_results = legal_search.invoke(state["user_request"])
    except Exception as e:
        print(f"Legal search failed: {e}")
        search_results = "Search unavailable."

    try:
        structured_trivia = chain.invoke({"user_request": state["user_request"], "search_results": search_results})
    except Exception as e:
        print(f"Trivia generation failed: {e}")
        structured_trivia = LegalTriviaOutput(trivia=[])

    return {"legal_trivia": structured_trivia}

# --- Build Graph ---
workflow = StateGraph(LegalAgentState)
workflow.add_node("generate_legal_doc", generate_legal_doc)
workflow.add_node("get_legal_trivia", get_legal_trivia)
workflow.set_entry_point("generate_legal_doc")
workflow.add_edge("generate_legal_doc", "get_legal_trivia")
workflow.add_edge("get_legal_trivia", END)
legal_agent = workflow.compile()
