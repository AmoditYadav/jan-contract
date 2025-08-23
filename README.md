
# Jan-Contract: Your Digital Workforce Assistant 🇮🇳

Jan-Contract is a multi-functional AI-powered platform designed to empower India's informal workforce. It provides accessible tools to create simple digital agreements, discover relevant government schemes, and understand complex legal documents, all through a simple web interface.

## 🚀 Key Features

This application is a unified suite of three powerful agents:

1.  **📝 Contract Generator**
    *   Creates simple, clear digital agreements from plain-text descriptions (e.g., "Paint my house for ₹5000").
    *   Provides contextually relevant legal trivia based on the agreement's content.
    *   Generates a professionally formatted, downloadable **PDF** of the final agreement.
    *   Captures undeniable proof of consent with a **video recording** feature.

2.  **🏦 Government Scheme Finder**
    *   Takes a user's profile (e.g., "a woman farmer in Maharashtra") and finds relevant government schemes.
    *   Uses live web search to provide up-to-date information.
    *   Returns a structured list of schemes with descriptions and direct links to official government websites.

3.  **📜 Document Demystifier & Chat**
    *   **Analyze:** Upload any legal PDF document to receive a concise, easy-to-understand summary and a breakdown of key legal terms.
    *   **Chat:** After the analysis, engage in an interactive Q&A session with the document to clarify specific doubts.

## 🛠️ Tech Stack

*   **Frontend:** Streamlit
*   **Backend API:** FastAPI
*   **AI Orchestration:** LangChain & LangGraph
*   **LLMs:** Google Gemini, Llama 3 (via Groq)
*   **Embeddings:** `FastEmbed` (BAAI/bge-base-en-v1.5)
*   **Vector Store:** FAISS (for in-memory semantic search)
*   **Tools & Libraries:**
    *   Tavily AI (for live web search)
    *   `fpdf2` (for PDF generation)
    *   `streamlit-webrtc` (for video recording)
    *   PyMuPDF (for reading PDFs)

## 📂 Project Structure

```
D:\jan-contract
|
+-- agents
|   +-- legal_agent.py
|   +-- scheme_chatbot.py
|   +-- demystifier_agent.py
|
+-- components
|   +-- video_recorder.py
|
+-- core_utils
|   +-- core_model_loaders.py
|
+-- tools
|   +-- legal_tools.py
|   +-- scheme_tools.py
|
+-- utils
|   +-- model_loaders.py
|   +-- pdf_generator.py
|
+-- .env               # Your secret API keys
+-- requirements.txt   # Project dependencies
+-- main_streamlit.py  # The main frontend application
+-- main_fastapi.py    # The backend API server
+-- README.md          # This file
```

## ⚙️ Setup and Installation

Follow these steps to set up and run the project on your local machine.

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd jan-contract
```

### 2. Create and Activate a Python Virtual Environment

This keeps your project dependencies isolated.

```bash
# Create the virtual environment
python -m venv venv

# Activate it (on Windows)
venv\Scripts\activate

# On MacOS/Linux, you would use:
# source venv/bin/activate
```

### 3. Install Dependencies

Install all the required Python libraries from the `requirements.txt` file.

```bash
pip install -r requirements.txt
```

### 4. Set Up Your API Keys

You will need API keys from Google, Tavily, and Groq.

1.  Create a file named `.env` in the root of the project directory.
2.  Copy and paste the following content into the `.env` file, replacing the placeholders with your actual keys.

```env
# D:\jan-contract\.env

GOOGLE_API_KEY="YOUR_GOOGLE_AI_STUDIO_API_KEY"
TAVILY_API_KEY="YOUR_TAVILY_AI_API_KEY"
GROQ_API_KEY="YOUR_GROQ_API_KEY"
```
**Important:** The `.env` file contains secrets and should **never** be committed to GitHub. Ensure `.env` is listed in your `.gitignore` file.

## ▶️ How to Run the Application

You can run the Streamlit frontend and the FastAPI backend independently.

### 1. Running the Streamlit Web App (Frontend)

This is the main user interface for the project.

```bash
streamlit run main_streamlit.py```

Your browser will automatically open a new tab with the application running.

### 2. Running the FastAPI Server (Backend API)

This exposes the project's logic as a professional API.

```bash
uvicorn main_fastapi:app --reload
```
*   The API server will be running at `http://127.0.0.1:8000`.
*   You can access the interactive API documentation (powered by Swagger UI) at **`http://127.0.0.1:8000/docs`**.
