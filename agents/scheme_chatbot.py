# D:\jan-contract\agents\scheme_chatbot.py

import os
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
from typing import List

# --- Tool and NEW Core Model Loader Imports ---
from tools.scheme_tools import scheme_search
from core_utils.core_model_loaders import load_gemini_llm

# --- Pydantic Models (No Changes) ---
class GovernmentScheme(BaseModel):
    scheme_name: str = Field(description="The official name of the government scheme.")
    description: str = Field(description="A concise summary of the scheme's objectives and benefits.")
    target_audience: str = Field(description="Who the scheme is intended for (e.g., Women, Farmers, PwD).")
    official_link: str = Field(description="The full, working URL to the official government scheme page or portal.")

class SchemeOutput(BaseModel):
    schemes: List[GovernmentScheme] = Field(description="A list of relevant government schemes.")

# --- Setup Models and Parsers ---
parser = PydanticOutputParser(pydantic_object=SchemeOutput)

# --- Initialize the LLM by calling the backend-safe loader function ---
llm = load_gemini_llm()

# --- Prompt Template (No Changes) ---
prompt = PromptTemplate(
    template="""
    You are an expert assistant for Indian government schemes...
    User Profile: {user_profile}
    Web search results: {search_results}
    {format_instructions}
    """,
    input_variables=["user_profile", "search_results"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)

# --- Build Chain (No Changes) ---
def get_search_results(query: dict):
    return scheme_search.invoke(query["user_profile"])

scheme_chatbot = (
    {"search_results": get_search_results, "user_profile": RunnablePassthrough()}
    | prompt
    | llm
    | parser
)