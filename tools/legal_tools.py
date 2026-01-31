# D:\jan-contract\tools\legal_tools.py

import os
from dotenv import load_dotenv
from langchain.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults

load_dotenv()

# Safely set environment variable only if it exists
tavily_key = os.getenv("TAVILY_API_KEY")
if tavily_key:
    os.environ["TAVILY_API_KEY"] = tavily_key

@tool
def legal_search(query: str):
    """
    Searches for legal information and relevant sections for a given query in the Indian context.
    Use this tool to find legal trivia and sections related to agreements.
    """
    # Increased max_results to 5 for more comprehensive context
    tavily_search = TavilySearchResults(max_results=5)
    results = tavily_search.invoke(f"Indian law and sections for: {query}")
    return results