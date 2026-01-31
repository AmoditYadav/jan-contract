# Enhanced FastAPI Application for Jan-Contract
# Comprehensive API for India's informal workforce

import os
import uuid
import tempfile
import json
import datetime
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, UploadFile, File, HTTPException, Form, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
import io
import shutil
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import all backend logic and agents
from agents.legal_agent import legal_agent
from agents.scheme_chatbot import scheme_chatbot
from agents.demystifier_agent import process_document_for_demystification
from agents.general_assistant_agent import ask_gemini
from utils.pdf_generator import generate_formatted_pdf

# Initialize FastAPI App
app = FastAPI(
    title="Jan-Contract Enhanced API",
    description="""
    🏗️ **Enhanced API for India's Informal Workforce**
    
    This comprehensive API provides four core functionalities:
    
    1. **Contract Generator**: Create digital agreements from plain text descriptions
    2. **Scheme Finder**: Discover relevant government schemes and benefits  
    3. **PDF Demystifier**: AI-powered analysis and explanation of legal documents
    4. **General Chatbot**: AI-powered assistance for general queries
    
    Built with FastAPI, LangChain, and modern AI technologies.
    """,
    version="2.1.0",
    contact={
        "name": "Jan-Contract Team",
        "email": "support@jan-contract.com"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    }
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Files
app.mount("/static", StaticFiles(directory="static"), name="static")

# =============================================================================
# PYDANTIC MODELS FOR REQUEST/RESPONSE VALIDATION
# =============================================================================

class ContractRequest(BaseModel):
    user_request: str = Field(
        ..., 
        description="Plain text description of the agreement needed", 
        min_length=10,
        max_length=2000,
        example="I need a contract for hiring a domestic helper for 6 months with weekly payment of Rs. 3000"
    )
    
    @validator('user_request')
    def validate_request(cls, v):
        if len(v.strip()) < 10:
            raise ValueError('Request must be at least 10 characters long')
        return v.strip()

class SchemeRequest(BaseModel):
    user_profile: str = Field(
        ..., 
        description="Description of user's situation, needs, or profile", 
        min_length=10,
        max_length=2000,
        example="I am a 35-year-old woman from rural Maharashtra, working as a daily wage laborer, looking for financial assistance schemes"
    )
    
    @validator('user_profile')
    def validate_profile(cls, v):
        if len(v.strip()) < 10:
            raise ValueError('Profile must be at least 10 characters long')
        return v.strip()

class ChatRequest(BaseModel):
    session_id: str = Field(
        ..., 
        description="Unique session identifier for document chat",
        example="123e4567-e89b-12d3-a456-426614174000"
    )
    question: str = Field(
        ..., 
        description="Question about the uploaded document", 
        min_length=1,
        max_length=1000,
        example="What are the key terms I should be aware of in this contract?"
    )

class GeneralChatRequest(BaseModel):
    question: str = Field(
        ..., 
        description="General question for AI assistant", 
        min_length=1,
        max_length=1000,
        example="What are my rights as a domestic worker in India?"
    )

class VideoConsentRequest(BaseModel):
    contract_id: str = Field(..., description="Identifier for the contract this consent applies to")
    consent_text: str = Field(..., description="Text of the consent being recorded", min_length=1)

# Response Models
class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now().isoformat())

class HealthCheck(BaseModel):
    status: str
    version: str
    timestamp: str
    services: Dict[str, Any]

# =============================================================================
# STATE MANAGEMENT
# =============================================================================

SESSION_CACHE = {}
CONTRACT_CACHE = {}

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_session_data(session_id: str):
    """Get session data or raise 404 if not found"""
    session_data = SESSION_CACHE.get(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found. Please upload the document again.")
    return session_data

def get_contract_data(contract_id: str):
    """Get contract data or raise 404 if not found"""
    contract_data = CONTRACT_CACHE.get(contract_id)
    if not contract_data:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract_data

# =============================================================================
# HEALTH CHECK ENDPOINT
# =============================================================================

@app.get("/health", tags=["System"], response_model=HealthCheck)
async def health_check():
    """Check the health status of the API and its dependencies"""
    
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
    
    # Check API keys
    api_keys = {
        "GOOGLE_API_KEY": "✅" if os.getenv("GOOGLE_API_KEY") else "❌",
        "GROQ_API_KEY": "✅" if os.getenv("GROQ_API_KEY") else "❌",
        "TAVILY_API_KEY": "✅" if os.getenv("TAVILY_API_KEY") else "❌"
    }
    
    return HealthCheck(
        status="healthy",
        version="2.1.0",
        timestamp=datetime.datetime.now().isoformat(),
        services={
            "directories": directories,
            "modules": modules,
            "api_keys": api_keys
        }
    )

# =============================================================================
# 1. CONTRACT GENERATOR ENDPOINTS
# =============================================================================

@app.post("/api/v1/contracts/generate", tags=["Contract Generator"], response_model=ApiResponse)
async def generate_contract(request: ContractRequest):
    """
    Generate a digital contract from plain text description.
    
    **Features:**
    - Creates structured legal documents
    - Includes relevant legal trivia and rights
    - Returns contract ID for future reference
    - Caches contract for retrieval
    
    **Use Cases:**
    - Domestic worker agreements
    - Service contracts
    - Rental agreements
    - Employment contracts
    """
    try:
        logger.info(f"Generating contract for request: {request.user_request[:100]}...")
        
        result = legal_agent.invoke({"user_request": request.user_request})
        
        # Cache the contract for later use
        contract_id = str(uuid.uuid4())
        CONTRACT_CACHE[contract_id] = {
            **result,
            "created_at": datetime.datetime.now().isoformat(),
            "user_request": request.user_request
        }
        
        return ApiResponse(
            success=True,
            message="Contract generated successfully",
            data={
                "contract_id": contract_id,
                "contract": result.get('legal_doc', ''),
                "legal_trivia": result.get('legal_trivia', {}),
                "created_at": datetime.datetime.now().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Contract generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Contract generation failed: {str(e)}")

@app.post("/api/v1/contracts/generate-pdf", tags=["Contract Generator"])
async def generate_contract_pdf(request: ContractRequest):
    """
    Generate a contract and return it as a downloadable PDF file.
    
    **Features:**
    - Creates formatted PDF document
    - Includes all contract terms and legal trivia
    - Returns downloadable file
    - Auto-generates filename with timestamp
    """
    try:
        logger.info(f"Generating PDF contract for request: {request.user_request[:100]}...")
        
        result = legal_agent.invoke({"user_request": request.user_request})
        contract_text = result.get('legal_doc', "Error: Could not generate document text.")
        
        pdf_bytes = generate_formatted_pdf(contract_text)
        
        filename = f"contract_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment;filename={filename}"}
        )
    except Exception as e:
        logger.error(f"PDF generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

@app.get("/api/v1/contracts/{contract_id}", tags=["Contract Generator"], response_model=ApiResponse)
async def get_contract(contract_id: str):
    """Retrieve a previously generated contract by ID"""
    contract_data = get_contract_data(contract_id)
    
    return ApiResponse(
        success=True,
        message="Contract retrieved successfully",
        data=contract_data
    )

@app.get("/api/v1/contracts", tags=["Contract Generator"], response_model=ApiResponse)
async def list_contracts():
    """List all generated contracts with summaries"""
    contracts = []
    for contract_id, contract_data in CONTRACT_CACHE.items():
        contracts.append({
            "id": contract_id,
            "summary": contract_data.get('legal_doc', '')[:100] + "...",
            "created_at": contract_data.get('created_at', 'Unknown'),
            "user_request": contract_data.get('user_request', '')[:100] + "..."
        })
    
    return ApiResponse(
        success=True,
        message=f"Found {len(contracts)} contract(s)",
        data={"contracts": contracts}
    )

@app.delete("/api/v1/contracts/{contract_id}", tags=["Contract Generator"], response_model=ApiResponse)
async def delete_contract(contract_id: str):
    """Delete a specific contract and its associated data"""
    contract_data = get_contract_data(contract_id)
    
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

# =============================================================================
# 2. SCHEME FINDER ENDPOINTS
# =============================================================================

@app.post("/api/v1/schemes/find", tags=["Scheme Finder"], response_model=ApiResponse)
async def find_schemes(request: SchemeRequest):
    """
    Find relevant government schemes based on user profile.
    
    **Features:**
    - Searches official government portals
    - Returns structured scheme information
    - Includes official links and descriptions
    - Targets specific user demographics
    
    **Use Cases:**
    - Financial assistance programs
    - Healthcare schemes
    - Education benefits
    - Employment support
    - Women's empowerment programs
    """
    try:
        logger.info(f"Finding schemes for profile: {request.user_profile[:100]}...")
        
        response = scheme_chatbot.invoke({"user_profile": request.user_profile})
        
        return ApiResponse(
            success=True,
            message="Schemes found successfully",
            data=response
        )
    except Exception as e:
        logger.error(f"Scheme search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Scheme search failed: {str(e)}")

# =============================================================================
# 3. PDF DEMYSTIFIER ENDPOINTS
# =============================================================================

@app.post("/api/v1/demystify/upload", tags=["PDF Demystifier"], response_model=ApiResponse)
async def demystify_upload(file: UploadFile = File(...)):
    """
    Upload a PDF document for AI-powered analysis.
    
    **Features:**
    - Analyzes legal documents with AI
    - Generates comprehensive reports
    - Creates interactive Q&A session
    - Explains complex legal terms
    
    **Supported Formats:**
    - PDF files only
    - Maximum size: 50MB
    
    **Analysis Includes:**
    - Document summary
    - Key legal terms explanation
    - Overall advice and recommendations
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF.")
    
    if file.size and file.size > 50 * 1024 * 1024:  # 50MB limit
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 50MB.")

    try:
        logger.info(f"Processing document: {file.filename}")
        
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
            "upload_time": datetime.datetime.now().isoformat(),
            "filename": file.filename
        }

        return ApiResponse(
            success=True,
            message="Document uploaded and analyzed successfully",
            data={
                "session_id": session_id,
                "report": analysis_result["report"],
                "filename": file.filename,
                "upload_time": datetime.datetime.now().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Document processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")

@app.post("/api/v1/demystify/chat", tags=["PDF Demystifier"], response_model=ApiResponse)
async def demystify_chat(request: ChatRequest):
    """
    Ask follow-up questions about an uploaded document.
    
    **Features:**
    - Interactive Q&A about uploaded documents
    - Context-aware responses
    - Legal term explanations
    - Document-specific insights
    
    **Requirements:**
    - Valid session ID from upload endpoint
    - Questions must be related to the uploaded document
    """
    session_data = get_session_data(request.session_id)
    
    try:
        logger.info(f"Processing question for session {request.session_id}: {request.question[:50]}...")
        
        rag_chain = session_data["rag_chain"]
        response = rag_chain.invoke(request.question)
        
        return ApiResponse(
            success=True,
            message="Question answered successfully",
            data={
                "answer": response,
                "session_id": request.session_id,
                "question": request.question
            }
        )
    except Exception as e:
        logger.error(f"Chat processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@app.get("/api/v1/demystify/sessions", tags=["PDF Demystifier"], response_model=ApiResponse)
async def list_demystify_sessions():
    """List all active document analysis sessions"""
    sessions = []
    for session_id, session_data in SESSION_CACHE.items():
        sessions.append({
            "session_id": session_id,
            "filename": session_data.get("filename", "Unknown"),
            "upload_time": session_data.get("upload_time", "Unknown")
        })
    
    return ApiResponse(
        success=True,
        message=f"Found {len(sessions)} active session(s)",
        data={"sessions": sessions}
    )

@app.delete("/api/v1/demystify/sessions/{session_id}", tags=["PDF Demystifier"], response_model=ApiResponse)
async def delete_demystify_session(session_id: str):
    """Delete a document analysis session and its associated files"""
    session_data = get_session_data(session_id)
    
    # Remove session
    del SESSION_CACHE[session_id]
    
    # Remove associated file
    file_path = session_data.get("file_path")
    if file_path and os.path.exists(file_path):
        os.remove(file_path)
    
    return ApiResponse(
        success=True,
        message="Session and associated files deleted successfully"
    )

# =============================================================================
# 4. GENERAL CHATBOT ENDPOINTS
# =============================================================================

@app.post("/api/v1/assistant/chat", tags=["General Assistant"], response_model=ApiResponse)
async def general_chat(request: GeneralChatRequest):
    """
    Get AI-powered assistance for general questions.
    
    **Features:**
    - Uses Google Gemini AI model
    - Provides helpful responses to general queries
    - Supports various topics and questions
    - Context-aware assistance
    
    **Use Cases:**
    - Legal rights information
    - General guidance
    - FAQ responses
    - Educational content
    """
    try:
        logger.info(f"Processing general chat question: {request.question[:50]}...")
        
        response = ask_gemini(request.question)
        
        return ApiResponse(
            success=True,
            message="Response generated successfully",
            data={
                "response": response,
                "question": request.question
            }
        )
    except Exception as e:
        logger.error(f"AI response generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI response generation failed: {str(e)}")

# =============================================================================
# MEDIA PROCESSING ENDPOINTS (BONUS)
# =============================================================================

@app.post("/api/v1/media/upload-video", tags=["Media Processing"], response_model=ApiResponse)
async def upload_video_consent(
    file: UploadFile = File(...),
    contract_id: str = Form(...),
    consent_text: str = Form(...)
):
    """
    Upload a video consent file for a specific contract.
    
    **Features:**
    - Supports multiple video formats
    - Links to specific contracts
    - Stores consent text metadata
    - File size validation
    
    **Supported Formats:**
    - MP4, AVI, MOV
    - Maximum size: 100MB
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
        logger.info(f"Uploading video consent for contract {contract_id}")
        
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
                "size": file.size,
                "consent_text": consent_text
            }
        )
    except Exception as e:
        logger.error(f"Video upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Video upload failed: {str(e)}")

@app.get("/api/v1/media/videos/{contract_id}", tags=["Media Processing"], response_model=ApiResponse)
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
                    "created": datetime.datetime.now().isoformat()
                })
        
        return ApiResponse(
            success=True,
            message=f"Found {len(videos)} video(s) for contract",
            data={"videos": videos}
        )
    except Exception as e:
        logger.error(f"Video retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Video retrieval failed: {str(e)}")

# =============================================================================
# ROOT ENDPOINT
# =============================================================================

@app.get("/", tags=["System"])
async def root():
    """Serve the Single Page Application"""
    return FileResponse("static/index.html")

@app.get("/api/info", tags=["System"])
async def api_info():
    """API information endpoint"""
    return {
        "message": "Jan-Contract Enhanced API",
        "version": "2.1.0",
        "description": "Comprehensive API for India's informal workforce",
        "docs": "/docs"
    }

# =============================================================================
# ERROR HANDLERS
# =============================================================================

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
    logger.error(f"Unhandled exception: {str(exc)}")
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
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)