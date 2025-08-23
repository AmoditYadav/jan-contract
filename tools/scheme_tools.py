# D:\jan-contract\tools\scheme_tools.py

import os
from dotenv import load_dotenv
from langchain.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults

load_dotenv()
os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")

@tool
def scheme_search(query: str):
    """
    Searches for government schemes based on a user's profile.
    Use this tool to find relevant government schemes for a user.
    """
    # Increased max_results to 7 to find content from more sources
    tavily_search = TavilySearchResults(max_results=7)
    results = tavily_search.invoke(f"official government schemes for {query} in India site:gov.in OR site:nic.in")
    return results