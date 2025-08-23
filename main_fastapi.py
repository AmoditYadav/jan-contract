# D:\jan-contract\main_fastapi.py

import os
import uuid
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import io

# --- Import all our backend logic and agents ---
from agents.legal_agent import legal_agent
from agents.scheme_chatbot import scheme_chatbot
from agents.demystifier_agent import process_document_for_demystification
from utils.pdf_generator import generate_formatted_pdf

# --- 1. Initialize FastAPI App ---
app = FastAPI(
    title="Jan-Contract API",
    description="A comprehensive API for generating digital contracts, finding government schemes, and analyzing legal documents for India's informal workforce.",
    version="1.0.0",
)

# --- 2. Pydantic Models for Request Bodies ---
# These models provide automatic data validation and documentation for our API.
class ContractRequest(BaseModel):
    user_request: str

class SchemeRequest(BaseModel):
    user_profile: str

class ChatRequest(BaseModel):
    session_id: str
    question: str

# --- 3. State Management for the Demystifier Chat ---
# This is a simple in-memory cache for a hackathon. For production, you would
# use a more robust cache like Redis.
SESSION_CACHE = {}

# --- 4. API Endpoints ---

@app.post("/generate-contract/json", tags=["Contract Generator"])
async def generate_contract_json(request: ContractRequest):
    """
    Takes a plain-text description and returns a structured JSON object
    containing the generated contract text (in Markdown) and relevant legal trivia.
    """
    try:
        result = legal_agent.invoke({"user_request": request.user_request})
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

@app.post("/generate-contract/pdf", tags=["Contract Generator"])
async def generate_contract_pdf(request: ContractRequest):
    """
    Takes a plain-text description, generates a contract, and returns it
    directly as a downloadable PDF file.
    """
    try:
        result = legal_agent.invoke({"user_request": request.user_request})
        contract_text = result.get('legal_doc', "Error: Could not generate document text.")
        
        pdf_bytes = generate_formatted_pdf(contract_text)
        
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment;filename=digital_agreement.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

@app.post("/find-schemes", tags=["Scheme Finder"])
async def find_schemes(request: SchemeRequest):
    """
    Takes a user profile description and returns a list of relevant
    government schemes with names, descriptions, and official links.
    """
    try:
        response = scheme_chatbot.invoke({"user_profile": request.user_profile})
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

@app.post("/demystify/upload", tags=["Document Demystifier"])
async def demystify_upload(file: UploadFile = File(...)):
    """
    Upload a PDF document for analysis. This endpoint processes the document,
    creates a RAG chain for chatting, and returns the initial analysis report
    along with a unique `session_id` for follow-up questions.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF.")

    try:
        # Use a temporary file to save the upload, as our loader needs a file path
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name
        
        analysis_result = process_document_for_demystification(tmp_path)
        
        # Clean up the temporary file
        os.unlink(tmp_path)

        # Create a unique session ID and cache the RAG chain
        session_id = str(uuid.uuid4())
        SESSION_CACHE[session_id] = analysis_result["rag_chain"]

        return {
            "session_id": session_id,
            "report": analysis_result["report"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process document: {e}")

@app.post("/demystify/chat", tags=["Document Demystifier"])
async def demystify_chat(request: ChatRequest):
    """
    Ask a follow-up question to a previously uploaded document.
    Requires the `session_id` returned by the /demystify/upload endpoint.
    """
    rag_chain = SESSION_CACHE.get(request.session_id)
    if not rag_chain:
        raise HTTPException(status_code=404, detail="Session not found. Please upload the document again.")
    
    try:
        response = rag_chain.invoke(request.question)
        return {"answer": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during chat: {e}")