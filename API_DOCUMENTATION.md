# Jan-Contract Enhanced API Documentation

## Overview

The Jan-Contract Enhanced API provides comprehensive services for India's informal workforce, including contract generation, scheme discovery, document analysis, and AI-powered assistance.

**Base URL:** `http://localhost:8000`  
**API Version:** 2.1.0  
**Documentation:** `/docs` (Swagger UI) or `/redoc` (ReDoc)

---

## Table of Contents

1. [Authentication & Setup](#authentication--setup)
2. [Contract Generator API](#contract-generator-api)
3. [Scheme Finder API](#scheme-finder-api)
4. [PDF Demystifier API](#pdf-demystifier-api)
5. [General Assistant API](#general-assistant-api)
6. [Media Processing API](#media-processing-api)
7. [System Endpoints](#system-endpoints)
8. [Error Handling](#error-handling)
9. [Testing Examples](#testing-examples)

---

## Authentication & Setup

### Environment Variables Required

```bash
GOOGLE_API_KEY=your_google_api_key
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
```

### Health Check

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "version": "2.1.0",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "services": {
    "directories": {
      "video_consents": true,
      "pdfs_demystify": true
    },
    "modules": {
      "streamlit_webrtc": "✅",
      "av": "✅",
      "speech_recognition": "✅"
    },
    "api_keys": {
      "GOOGLE_API_KEY": "✅",
      "GROQ_API_KEY": "✅",
      "TAVILY_API_KEY": "✅"
    }
  }
}
```

---

## Contract Generator API

### 1. Generate Contract

**Endpoint:** `POST /api/v1/contracts/generate`

**Description:** Generate a digital contract from plain text description.

**Request Payload:**
```json
{
  "user_request": "I need a contract for hiring a domestic helper for 6 months with weekly payment of Rs. 3000"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Contract generated successfully",
  "data": {
    "contract_id": "123e4567-e89b-12d3-a456-426614174000",
    "contract": "DOMESTIC HELPER EMPLOYMENT AGREEMENT\n\nThis agreement is made between...",
    "legal_trivia": {
      "trivia": [
        {
          "point": "Minimum wage rights for domestic workers",
          "explanation": "Domestic workers are entitled to minimum wages as per state regulations",
          "source_url": "https://labour.gov.in/sites/default/files/domestic_workers_act.pdf"
        }
      ]
    },
    "created_at": "2024-01-15T10:30:00.000Z"
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### 2. Generate Contract PDF

**Endpoint:** `POST /api/v1/contracts/generate-pdf`

**Description:** Generate a contract and return it as a downloadable PDF file.

**Request Payload:**
```json
{
  "user_request": "I need a contract for hiring a domestic helper for 6 months with weekly payment of Rs. 3000"
}
```

**Response:** PDF file download with headers:
```
Content-Type: application/pdf
Content-Disposition: attachment;filename=contract_20240115_103000.pdf
```

### 3. Get Contract

**Endpoint:** `GET /api/v1/contracts/{contract_id}`

**Description:** Retrieve a previously generated contract by ID.

**Response:**
```json
{
  "success": true,
  "message": "Contract retrieved successfully",
  "data": {
    "legal_doc": "DOMESTIC HELPER EMPLOYMENT AGREEMENT\n\nThis agreement is made between...",
    "legal_trivia": {
      "trivia": [...]
    },
    "created_at": "2024-01-15T10:30:00.000Z",
    "user_request": "I need a contract for hiring a domestic helper..."
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### 4. List Contracts

**Endpoint:** `GET /api/v1/contracts`

**Description:** List all generated contracts with summaries.

**Response:**
```json
{
  "success": true,
  "message": "Found 2 contract(s)",
  "data": {
    "contracts": [
      {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "summary": "DOMESTIC HELPER EMPLOYMENT AGREEMENT\n\nThis agreement is made between...",
        "created_at": "2024-01-15T10:30:00.000Z",
        "user_request": "I need a contract for hiring a domestic helper for 6 months..."
      }
    ]
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### 5. Delete Contract

**Endpoint:** `DELETE /api/v1/contracts/{contract_id}`

**Description:** Delete a specific contract and its associated data.

**Response:**
```json
{
  "success": true,
  "message": "Contract and associated data deleted successfully",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

---

## Scheme Finder API

### Find Government Schemes

**Endpoint:** `POST /api/v1/schemes/find`

**Description:** Find relevant government schemes based on user profile.

**Request Payload:**
```json
{
  "user_profile": "I am a 35-year-old woman from rural Maharashtra, working as a daily wage laborer, looking for financial assistance schemes"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Schemes found successfully",
  "data": {
    "schemes": [
      {
        "scheme_name": "Pradhan Mantri Jan Dhan Yojana",
        "description": "Financial inclusion program providing basic banking services to unbanked households",
        "target_audience": "Unbanked households, especially women",
        "official_link": "https://pmjdy.gov.in/"
      },
      {
        "scheme_name": "Mahila Shakti Kendra",
        "description": "Women empowerment scheme providing support for rural women",
        "target_audience": "Rural women",
        "official_link": "https://wcd.nic.in/schemes/mahila-shakti-kendra"
      }
    ]
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

---

## PDF Demystifier API

### 1. Upload Document

**Endpoint:** `POST /api/v1/demystify/upload`

**Description:** Upload a PDF document for AI-powered analysis.

**Request:** Multipart form data
- `file`: PDF file (max 50MB)

**Response:**
```json
{
  "success": true,
  "message": "Document uploaded and analyzed successfully",
  "data": {
    "session_id": "456e7890-e89b-12d3-a456-426614174001",
    "report": {
      "summary": "This is a rental agreement for a residential property...",
      "key_terms": [
        {
          "term": "Security Deposit",
          "explanation": "A refundable amount paid by tenant to cover potential damages",
          "resource_link": "https://housing.com/guides/security-deposit"
        }
      ],
      "overall_advice": "This is an automated analysis. For critical matters, please consult with a qualified legal professional."
    },
    "filename": "rental_agreement.pdf",
    "upload_time": "2024-01-15T10:30:00.000Z"
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### 2. Chat with Document

**Endpoint:** `POST /api/v1/demystify/chat`

**Description:** Ask follow-up questions about an uploaded document.

**Request Payload:**
```json
{
  "session_id": "456e7890-e89b-12d3-a456-426614174001",
  "question": "What are the key terms I should be aware of in this contract?"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Question answered successfully",
  "data": {
    "answer": "Based on the document, the key terms you should be aware of include: 1. Security Deposit - A refundable amount...",
    "session_id": "456e7890-e89b-12d3-a456-426614174001",
    "question": "What are the key terms I should be aware of in this contract?"
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### 3. List Sessions

**Endpoint:** `GET /api/v1/demystify/sessions`

**Description:** List all active document analysis sessions.

**Response:**
```json
{
  "success": true,
  "message": "Found 1 active session(s)",
  "data": {
    "sessions": [
      {
        "session_id": "456e7890-e89b-12d3-a456-426614174001",
        "filename": "rental_agreement.pdf",
        "upload_time": "2024-01-15T10:30:00.000Z"
      }
    ]
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### 4. Delete Session

**Endpoint:** `DELETE /api/v1/demystify/sessions/{session_id}`

**Description:** Delete a document analysis session and its associated files.

**Response:**
```json
{
  "success": true,
  "message": "Session and associated files deleted successfully",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

---

## General Assistant API

### Chat with AI Assistant

**Endpoint:** `POST /api/v1/assistant/chat`

**Description:** Get AI-powered assistance for general questions.

**Request Payload:**
```json
{
  "question": "What are my rights as a domestic worker in India?"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Response generated successfully",
  "data": {
    "response": "As a domestic worker in India, you have several important rights: 1. Right to minimum wages as per state regulations...",
    "question": "What are my rights as a domestic worker in India?"
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

---

## Media Processing API

### 1. Upload Video Consent

**Endpoint:** `POST /api/v1/media/upload-video`

**Description:** Upload a video consent file for a specific contract.

**Request:** Multipart form data
- `file`: Video file (MP4, AVI, MOV - max 100MB)
- `contract_id`: Contract identifier
- `consent_text`: Text of the consent being recorded

**Response:**
```json
{
  "success": true,
  "message": "Video consent uploaded successfully",
  "data": {
    "video_path": "video_consents/consent_123e4567-e89b-12d3-a456-426614174000_789.mp4",
    "contract_id": "123e4567-e89b-12d3-a456-426614174000",
    "filename": "consent_123e4567-e89b-12d3-a456-426614174000_789.mp4",
    "size": 2048576,
    "consent_text": "I agree to the terms and conditions of this employment contract"
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### 2. Get Contract Videos

**Endpoint:** `GET /api/v1/media/videos/{contract_id}`

**Description:** Get all video consents for a specific contract.

**Response:**
```json
{
  "success": true,
  "message": "Found 1 video(s) for contract",
  "data": {
    "videos": [
      {
        "filename": "consent_123e4567-e89b-12d3-a456-426614174000_789.mp4",
        "path": "video_consents/consent_123e4567-e89b-12d3-a456-426614174000_789.mp4",
        "size": 2048576,
        "created": "2024-01-15T10:30:00.000Z"
      }
    ]
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

---

## System Endpoints

### Root Endpoint

**Endpoint:** `GET /`

**Description:** API root endpoint with comprehensive information.

**Response:**
```json
{
  "message": "Jan-Contract Enhanced API",
  "version": "2.1.0",
  "description": "Comprehensive API for India's informal workforce",
  "features": [
    "Contract Generation",
    "Scheme Discovery",
    "Document Analysis",
    "AI Assistant",
    "Media Processing"
  ],
  "endpoints": {
    "health": "/health",
    "contracts": "/api/v1/contracts/generate",
    "schemes": "/api/v1/schemes/find",
    "demystify": "/api/v1/demystify/upload",
    "assistant": "/api/v1/assistant/chat",
    "media": "/api/v1/media/upload-video"
  },
  "docs": "/docs",
  "redoc": "/redoc"
}
```

---

## Error Handling

### Standard Error Response Format

```json
{
  "success": false,
  "message": "Request failed",
  "error": "Detailed error message",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### Common HTTP Status Codes

- `200 OK`: Request successful
- `400 Bad Request`: Invalid request data
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

### Validation Errors

```json
{
  "success": false,
  "message": "Request failed",
  "error": [
    {
      "loc": ["body", "user_request"],
      "msg": "ensure this value has at least 10 characters",
      "type": "value_error.any_str.min_length"
    }
  ],
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

---

## Testing Examples

### Using cURL

#### 1. Generate Contract
```bash
curl -X POST "http://localhost:8000/api/v1/contracts/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "user_request": "I need a contract for hiring a domestic helper for 6 months with weekly payment of Rs. 3000"
  }'
```

#### 2. Find Schemes
```bash
curl -X POST "http://localhost:8000/api/v1/schemes/find" \
  -H "Content-Type: application/json" \
  -d '{
    "user_profile": "I am a 35-year-old woman from rural Maharashtra, working as a daily wage laborer, looking for financial assistance schemes"
  }'
```

#### 3. Upload Document
```bash
curl -X POST "http://localhost:8000/api/v1/demystify/upload" \
  -F "file=@/path/to/document.pdf"
```

#### 4. Chat with Assistant
```bash
curl -X POST "http://localhost:8000/api/v1/assistant/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are my rights as a domestic worker in India?"
  }'
```

### Using Python requests

```python
import requests
import json

# Base URL
BASE_URL = "http://localhost:8000"

# 1. Generate Contract
contract_data = {
    "user_request": "I need a contract for hiring a domestic helper for 6 months with weekly payment of Rs. 3000"
}
response = requests.post(f"{BASE_URL}/api/v1/contracts/generate", json=contract_data)
print(response.json())

# 2. Find Schemes
scheme_data = {
    "user_profile": "I am a 35-year-old woman from rural Maharashtra, working as a daily wage laborer, looking for financial assistance schemes"
}
response = requests.post(f"{BASE_URL}/api/v1/schemes/find", json=scheme_data)
print(response.json())

# 3. Chat with Assistant
chat_data = {
    "question": "What are my rights as a domestic worker in India?"
}
response = requests.post(f"{BASE_URL}/api/v1/assistant/chat", json=chat_data)
print(response.json())

# 4. Upload Document
with open("document.pdf", "rb") as f:
    files = {"file": f}
    response = requests.post(f"{BASE_URL}/api/v1/demystify/upload", files=files)
    print(response.json())
```

### Using JavaScript/Fetch

```javascript
const BASE_URL = "http://localhost:8000";

// 1. Generate Contract
async function generateContract() {
  const response = await fetch(`${BASE_URL}/api/v1/contracts/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      user_request: "I need a contract for hiring a domestic helper for 6 months with weekly payment of Rs. 3000"
    })
  });
  const data = await response.json();
  console.log(data);
}

// 2. Find Schemes
async function findSchemes() {
  const response = await fetch(`${BASE_URL}/api/v1/schemes/find`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      user_profile: "I am a 35-year-old woman from rural Maharashtra, working as a daily wage laborer, looking for financial assistance schemes"
    })
  });
  const data = await response.json();
  console.log(data);
}

// 3. Chat with Assistant
async function chatWithAssistant() {
  const response = await fetch(`${BASE_URL}/api/v1/assistant/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      question: "What are my rights as a domestic worker in India?"
    })
  });
  const data = await response.json();
  console.log(data);
}
```

---

## Rate Limits & Best Practices

### Rate Limits
- No explicit rate limits implemented
- Recommended: 100 requests per minute per IP
- Large file uploads may take longer processing time

### Best Practices
1. **Always check the health endpoint** before making requests
2. **Use appropriate content types** for different endpoints
3. **Handle errors gracefully** with proper error checking
4. **Store session IDs** for document chat functionality
5. **Validate file sizes** before upload (50MB for PDFs, 100MB for videos)
6. **Use HTTPS in production** for security

### File Upload Guidelines
- **PDF files**: Maximum 50MB, only PDF format
- **Video files**: Maximum 100MB, formats: MP4, AVI, MOV
- **File naming**: Avoid special characters, use alphanumeric names

---

## Support & Contact

- **API Documentation**: `/docs` (Swagger UI)
- **Alternative Docs**: `/redoc` (ReDoc)
- **Health Check**: `/health`
- **Support Email**: support@jan-contract.com
- **Version**: 2.1.0

---

*This documentation is automatically generated and updated with each API version release.*
