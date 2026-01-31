import os
import time
import random
from google import genai
from google.genai import types

# Configure the API key from the .env file
try:
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    model_name = "gemini-2.0-flash-exp" # Using the user's preferred model
except Exception as e:
    print(f"Error configuring Google Gen AI Client: {e}")
    client = None
    model_name = None

def ask_gemini(prompt: str) -> str:
    """
    Sends a prompt directly to the Google Gen AI API using the new SDK.
    Includes robust retry logic for 429 Resource Exhausted errors.
    """
    if client is None:
        return "Error: The Gen AI client is not configured. Please check your API key."
    
    max_retries = 5
    base_delay = 2  # seconds

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            return response.text
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                if attempt == max_retries - 1:
                    return f"Error: Rate limit exceeded after {max_retries} attempts. Please try again later."
                
                # Exponential backoff with jitter
                delay = (base_delay * (2 ** attempt)) + random.uniform(0, 1)
                print(f"Rate limit hit. Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
            else:
                return f"An error occurred while communicating with the Gemini API: {str(e)}"
    
    return "Error: Failed to get response from Gemini API."