# D:\jan-contract\agents\scheme_chatbot.py

import os
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
from typing import List

# --- Tool and Core Model Loader Imports ---
from tools.scheme_tools import scheme_search
from core_utils.core_model_loaders import load_gemini_llm

# --- Pydantic Models ---
class GovernmentScheme(BaseModel):
    scheme_name: str = Field(description="The official name of the government scheme.")
    description: str = Field(description="A concise summary of the scheme's objectives and benefits.")
    target_audience: str = Field(description="Who the scheme is intended for (e.g., Women, Farmers, PwD).")
    official_link: str = Field(description="The full, working URL to the official government scheme page or portal.")

class SchemeOutput(BaseModel):
    schemes: List[GovernmentScheme] = Field(description="A list of relevant government schemes.")

# --- Setup Models and Parsers ---
parser = PydanticOutputParser(pydantic_object=SchemeOutput)

# --- Initialize the LLM ---
llm = load_gemini_llm()

# --- Prompt Template ---
prompt = PromptTemplate(
    template="""
    You are an expert assistant for Indian government schemes.
    Find the most relevant official government schemes for the profile below.
    Focus on accuracy and official sources.
    
    User Profile: {user_profile}
    Web search results: {search_results}
    
    {format_instructions}
    """,
    input_variables=["user_profile", "search_results"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)

# --- Build Chain ---
def get_search_results(query: dict):
    print(f"---NODE: Searching Schemes for profile: {query['user_profile']}---")
    try:
        return scheme_search.invoke(query["user_profile"])
    except Exception as e:
        print(f"Scheme search failed: {e}")
        return "Search unavailable."

scheme_chatbot = (
    {"search_results": get_search_results, "user_profile": RunnablePassthrough()}
    | prompt
    | llm
    | parser
)