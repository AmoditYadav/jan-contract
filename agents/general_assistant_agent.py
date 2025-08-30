# D:\jan-contract\agents\general_assistant_agent.py

import os
import google.generativeai as genai

# Configure the API key from the .env file
try:
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    # Use a specific, robust model name
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    print(f"Error configuring Google Generative AI: {e}")
    model = None

def ask_gemini(prompt: str) -> str:
    """
    Sends a prompt directly to the Google Gemini API and returns the text response.
    This is the core logic from your script, adapted for our application.
    """
    if model is None:
        return "Error: The Generative AI model is not configured. Please check your API key."
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"An error occurred while communicating with the Gemini API: {str(e)}"