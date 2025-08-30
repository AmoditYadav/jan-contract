# D:\jan-contract\main_fastapi.py

import os
import uuid
import tempfile
import json
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, HTTPException, Form, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import io
import shutil

# --- Import all our backend logic and agents ---
from agents.legal_agent import legal_agent
from agents.scheme_chatbot import scheme_chatbot
from agents.demystifier_agent import process_document_for_demystification
from agents.general_assistant_agent import ask_gemini
from utils.pdf_generator import generate_formatted_pdf

# --- 1. Initialize FastAPI App ---
app = FastAPI(
    title="Jan-Contract Unified API",
    description="""
    A comprehensive API for India's informal workforce providing:
    
    🏗️ **Contract Generation**: Create digital agreements from plain text
    🏦 **Scheme Discovery**: Find relevant government schemes and benefits
    📜 **Document Analysis**: Demystify legal documents with AI-powered insights
    🤖 **General Assistant**: AI-powered guidance and support
    🎥 **Media Processing**: Audio/video consent recording and processing
    
    Built with FastAPI, LangChain, and modern AI technologies.
    """,
    version="2.0.0",
    contact={
        "name": "Jan-Contract Team",
        "email": "support@jan-contract.com"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    }
)

# --- 2. CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 3. Pydantic Models for Request Bodies ---
class ContractRequest(BaseModel):
    user_request: str = Field(..., description="Plain text description of the agreement needed", min_length=10)
    
class SchemeRequest(BaseModel):
    user_profile: str = Field(..., description="Description of user's situation, needs, or profile", min_length=10)
    
class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Unique session identifier for document chat")
    question: str = Field(..., description="Question about the uploaded document", min_length=1)
    
class GeneralChatRequest(BaseModel):
    question: str = Field(..., description="General question for AI assistant", min_length=1)
    
class VideoConsentRequest(BaseModel):
    contract_id: str = Field(..., description="Identifier for the contract this consent applies to")
    consent_text: str = Field(..., description="Text of the consent being recorded", min_length=1)

# --- 4. Response Models ---
class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
    error: Optional[str] = None

class HealthCheck(BaseModel):
    status: str
    version: str
    timestamp: str
    services: dict

# --- 5. State Management ---
SESSION_CACHE = {}
CONTRACT_CACHE = {}

# --- 6. Health Check Endpoint ---
@app.get("/health", tags=["System"], response_model=HealthCheck)
async def health_check():
    """Check the health status of the API and its dependencies"""
    import datetime
    
    # Check if required directories exist
    directories = {
        "video_consents": os.path.exists("video_consents"),
        "pdfs_demystify": os.path.exists("pdfs_demystify")
    }
    
    # Check if required modules can be imported
    modules = {}
    try:
        import streamlit_webrtc
        modules["streamlit_webrtc"] = "✅"
    except:
        modules["streamlit_webrtc"] = "❌"
    
    try:
        import av
        modules["av"] = "✅"
    except:
        modules["av"] = "❌"
    
    try:
        import speech_recognition
        modules["speech_recognition"] = "✅"
    except:
        modules["speech_recognition"] = "❌"
    
    return HealthCheck(
        status="healthy",
        version="2.0.0",
        timestamp=datetime.datetime.now().isoformat(),
        services={
            "directories": directories,
            "modules": modules
        }
    )

# --- 7. Contract Generation Endpoints ---

@app.post("/contract/generate", tags=["Contract Generator"], response_model=ApiResponse)
async def generate_contract(request: ContractRequest):
    """
    Generate a digital contract from plain text description.
    Returns structured JSON with contract text and legal trivia.
    """
    try:
        result = legal_agent.invoke({"user_request": request.user_request})
        
        # Cache the contract for later use
        contract_id = str(uuid.uuid4())
        CONTRACT_CACHE[contract_id] = result
        
        return ApiResponse(
            success=True,
            message="Contract generated successfully",
            data={
                "contract_id": contract_id,
                "contract": result.get('legal_doc', ''),
                "legal_trivia": result.get('legal_trivia', {}),
                "timestamp": str(uuid.uuid4())
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Contract generation failed: {str(e)}")

@app.post("/contract/generate-pdf", tags=["Contract Generator"])
async def generate_contract_pdf(request: ContractRequest):
    """
    Generate a contract and return it as a downloadable PDF file.
    """
    try:
        result = legal_agent.invoke({"user_request": request.user_request})
        contract_text = result.get('legal_doc', "Error: Could not generate document text.")
        
        pdf_bytes = generate_formatted_pdf(contract_text)
        
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment;filename=digital_agreement_{uuid.uuid4()}.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

@app.get("/contract/{contract_id}", tags=["Contract Generator"], response_model=ApiResponse)
async def get_contract(contract_id: str):
    """Retrieve a previously generated contract by ID"""
    if contract_id not in CONTRACT_CACHE:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    return ApiResponse(
        success=True,
        message="Contract retrieved successfully",
        data=CONTRACT_CACHE[contract_id]
    )

# --- 8. Scheme Finder Endpoints ---

@app.post("/schemes/find", tags=["Scheme Finder"], response_model=ApiResponse)
async def find_schemes(request: SchemeRequest):
    """
    Find relevant government schemes based on user profile.
    Returns list of schemes with descriptions and official links.
    """
    try:
        response = scheme_chatbot.invoke({"user_profile": request.user_profile})
        return ApiResponse(
            success=True,
            message="Schemes found successfully",
            data=response
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scheme search failed: {str(e)}")

# --- 9. Document Demystifier Endpoints ---

@app.post("/demystify/upload", tags=["Document Demystifier"], response_model=ApiResponse)
async def demystify_upload(file: UploadFile = File(...)):
    """
    Upload a PDF document for AI-powered analysis.
    Returns analysis report and session ID for follow-up questions.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF.")
    
    if file.size and file.size > 50 * 1024 * 1024:  # 50MB limit
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 50MB.")

    try:
        # Save to project directory
        upload_dir = "pdfs_demystify"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, f"{uuid.uuid4()}_{file.filename}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process the document
        analysis_result = process_document_for_demystification(file_path)
        
        # Create session and cache RAG chain
        session_id = str(uuid.uuid4())
        SESSION_CACHE[session_id] = {
            "rag_chain": analysis_result["rag_chain"],
            "file_path": file_path,
            "upload_time": str(uuid.uuid4())
        }

        return ApiResponse(
            success=True,
            message="Document uploaded and analyzed successfully",
            data={
                "session_id": session_id,
                "report": analysis_result["report"],
                "filename": file.filename
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")

@app.post("/demystify/chat", tags=["Document Demystifier"], response_model=ApiResponse)
async def demystify_chat(request: ChatRequest):
    """
    Ask follow-up questions about an uploaded document.
    Requires valid session ID from upload endpoint.
    """
    session_data = SESSION_CACHE.get(request.session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found. Please upload the document again.")
    
    try:
        rag_chain = session_data["rag_chain"]
        response = rag_chain.invoke(request.question)
        
        return ApiResponse(
            success=True,
            message="Question answered successfully",
            data={"answer": response}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

# --- 10. General Assistant Endpoints ---

@app.post("/assistant/chat", tags=["General Assistant"], response_model=ApiResponse)
async def general_chat(request: GeneralChatRequest):
    """
    Get AI-powered assistance for general questions.
    Uses Gemini AI model for responses.
    """
    try:
        response = ask_gemini(request.question)
        return ApiResponse(
            success=True,
            message="Response generated successfully",
            data={"response": response}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI response generation failed: {str(e)}")

# --- 11. Media Processing Endpoints ---

@app.post("/media/upload-video", tags=["Media Processing"], response_model=ApiResponse)
async def upload_video_consent(
    file: UploadFile = File(...),
    contract_id: str = Form(...),
    consent_text: str = Form(...)
):
    """
    Upload a video consent file for a specific contract.
    Supports MP4, AVI, MOV formats.
    """
    allowed_types = ["video/mp4", "video/avi", "video/quicktime", "video/x-msvideo"]
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid video format. Allowed: {', '.join(allowed_types)}"
        )
    
    if file.size and file.size > 100 * 1024 * 1024:  # 100MB limit
        raise HTTPException(status_code=400, detail="Video too large. Maximum size is 100MB.")

    try:
        # Save video to project directory
        upload_dir = "video_consents"
        os.makedirs(upload_dir, exist_ok=True)
        
        video_filename = f"consent_{contract_id}_{uuid.uuid4()}.mp4"
        video_path = os.path.join(upload_dir, video_filename)
        
        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return ApiResponse(
            success=True,
            message="Video consent uploaded successfully",
            data={
                "video_path": video_path,
                "contract_id": contract_id,
                "filename": video_filename,
                "size": file.size
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video upload failed: {str(e)}")

@app.get("/media/videos/{contract_id}", tags=["Media Processing"], response_model=ApiResponse)
async def get_contract_videos(contract_id: str):
    """Get all video consents for a specific contract"""
    try:
        video_dir = "video_consents"
        if not os.path.exists(video_dir):
            return ApiResponse(
                success=True,
                message="No videos found",
                data={"videos": []}
            )
        
        videos = []
        for filename in os.listdir(video_dir):
            if filename.startswith(f"consent_{contract_id}_"):
                file_path = os.path.join(video_dir, filename)
                videos.append({
                    "filename": filename,
                    "path": file_path,
                    "size": os.path.getsize(file_path),
                    "created": str(uuid.uuid4())
                })
        
        return ApiResponse(
            success=True,
            message=f"Found {len(videos)} video(s) for contract",
            data={"videos": videos}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video retrieval failed: {str(e)}")

# --- 12. Utility Endpoints ---

@app.get("/contracts", tags=["Utilities"], response_model=ApiResponse)
async def list_contracts():
    """List all generated contracts"""
    contracts = []
    for contract_id, contract_data in CONTRACT_CACHE.items():
        contracts.append({
            "id": contract_id,
            "summary": contract_data.get('legal_doc', '')[:100] + "...",
            "timestamp": str(uuid.uuid4())
        })
    
    return ApiResponse(
        success=True,
        message=f"Found {len(contracts)} contract(s)",
        data={"contracts": contracts}
    )

@app.delete("/contracts/{contract_id}", tags=["Utilities"], response_model=ApiResponse)
async def delete_contract(contract_id: str):
    """Delete a specific contract and its associated data"""
    if contract_id not in CONTRACT_CACHE:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    # Remove contract
    del CONTRACT_CACHE[contract_id]
    
    # Remove associated videos
    video_dir = "video_consents"
    if os.path.exists(video_dir):
        for filename in os.listdir(video_dir):
            if filename.startswith(f"consent_{contract_id}_"):
                os.remove(os.path.join(video_dir, filename))
    
    return ApiResponse(
        success=True,
        message="Contract and associated data deleted successfully"
    )

@app.get("/", tags=["System"])
async def root():
    """API root endpoint with basic information"""
    return {
        "message": "Jan-Contract Unified API",
        "version": "2.0.0",
        "description": "Comprehensive API for India's informal workforce",
        "endpoints": {
            "health": "/health",
            "contracts": "/contract/generate",
            "schemes": "/schemes/find",
            "demystify": "/demystify/upload",
            "assistant": "/assistant/chat",
            "media": "/media/upload-video"
        },
        "docs": "/docs"
    }

# --- 13. Error Handlers ---

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiResponse(
            success=False,
            message="Request failed",
            error=str(exc.detail)
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content=ApiResponse(
            success=False,
            message="Internal server error",
            error="An unexpected error occurred"
        ).dict()
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)