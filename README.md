# Autonomous QA Agent

A production-quality **Autonomous QA Agent** that leverages **Google Gemini**, **LangChain**, and **FAISS** to automatically generate test cases and Selenium scripts from documentation using Retrieval-Augmented Generation (RAG).

## 🎯 Overview

This system combines state-of-the-art AI with established testing frameworks to:

1. **Build Knowledge Bases** from support documentation (MD, TXT, JSON, PDF) and HTML files
2. **Generate Test Cases** using RAG-powered AI that grounds all assertions in source documentation
3. **Create Selenium Scripts** automatically from test cases with strict selector validation

## 🏗️ Architecture

### Technology Stack

- **Backend Framework:** FastAPI
- **Frontend:** Streamlit
- **LLM:** Google Gemini 1.5 Pro via LangChain
- **Embeddings:** Google's `models/embedding-001` via LangChain
- **Vector Database:** FAISS (with disk persistence)
- **RAG Framework:** LangChain (PromptTemplate, RetrievalQA, LCEL)
- **HTML Parsing:** BeautifulSoup4 + lxml
- **PDF Parsing:** PyMuPDF
- **Document Loading:** LangChain Document Loaders
- **Text Splitting:** LangChain RecursiveCharacterTextSplitter
- **Selenium Generation:** LangChain LLM with strict prompting

### Repository Structure

```
autonomous-qa-agent/
├─ backend/
│  ├─ app.py                 # FastAPI application with 3 endpoints
│  ├─ models.py              # Pydantic models for validation
│  ├─ rag.py                 # RAG engine with Gemini
│  ├─ vectorstore.py         # FAISS vector store manager
│  ├─ parsers.py             # Document parsers (PDF, HTML, JSON, etc.)
│  ├─ selectors.py           # HTML selector extraction
│  ├─ selenium_gen.py        # Selenium script generator
│  ├─ settings.py            # Configuration management
│  └─ utils.py               # Utility functions
├─ frontend/
│  └─ streamlit_app.py       # 3-page Streamlit UI
├─ assets/
│  ├─ checkout.html          # Sample e-commerce checkout page
│  └─ support_docs/
│      ├─ product_specs.md   # Product specifications
│      ├─ ui_ux_guide.txt    # UI/UX design guide
│      └─ api_endpoints.json # API documentation
├─ scripts/
│  ├─ build_kb.py            # Knowledge base builder script
│  └─ demo_recording_steps.txt
├─ tests/
│  └─ smoke_tests.py         # Smoke tests
├─ faiss_index/              # FAISS vector store (created at runtime)
├─ requirements.txt
├─ .env                      # Environment variables (create this)
└─ README.md
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Google AI API key (get it from [Google AI Studio](https://makersuite.google.com/app/apikey))

### Installation

1. **Clone the repository:**

```bash
cd c:\Users\ASUS\Desktop\ML DL GenAI\OceanAI
```

2. **Create and activate virtual environment:**

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
```

4. **Create `.env` file in the root directory:**

```env
GOOGLE_API_KEY=your_google_api_key_here
```

### Build Knowledge Base

Before using the system, build the knowledge base from the sample documents:

```bash
python scripts/build_kb.py
```

This will:
- Parse all documents in `assets/support_docs/`
- Create embeddings using Google's embedding model
- Build and persist FAISS index to `faiss_index/`
- Extract selectors from `checkout.html`

### Run the Application

**Terminal 1 - Start FastAPI Backend:**

```bash
python backend/app.py
```

API will be available at: `http://localhost:8000`
API docs (Swagger): `http://localhost:8000/docs`

**Terminal 2 - Start Streamlit Frontend:**

```bash
streamlit run frontend/streamlit_app.py
```

UI will be available at: `http://localhost:8501`

## 📖 Usage Guide

### 1. Knowledge Base Builder

**Page:** Knowledge Base

**Steps:**
1. Upload support documents (MD, TXT, JSON, PDF)
2. Upload `checkout.html` file
3. Click "Build Knowledge Base"
4. View statistics: chunks created, sources processed, selectors extracted

**Output:**
- FAISS index saved to disk
- Selector map extracted from HTML
- Ready for test case generation

### 2. Test Case Generator

**Page:** Test Case Generator

**Steps:**
1. Enter a RAG query (e.g., "Generate all positive and negative test cases for discount code feature")
2. Adjust top_k (number of chunks to retrieve)
3. Click "Generate Test Cases"
4. Review generated test cases in table
5. Select a test case to view full details
6. Download test case as JSON

**Test Case Schema:**

```json
{
  "Test_ID": "TC-001",
  "Feature": "Discount Code",
  "Test_Scenario": "Apply valid discount code SAVE10",
  "Preconditions": ["User is on checkout page", "Cart has items"],
  "Steps": ["Enter code SAVE10", "Click Apply button"],
  "Expected_Result": "10% discount applied to subtotal",
  "Test_Type": "positive",
  "Grounded_In": ["product_specs.md (chunk_0)", "api_endpoints.json (chunk_2)"],
  "SelectorsNeeded": ["discount-code", "apply-btn", "discount-success"]
}
```

**Key Features:**
- All test cases are **grounded in source documentation**
- Missing information is marked as `"UNKNOWN"`
- No hallucinations - strict evidence-based generation
- Both positive and negative test cases

### 3. Selenium Script Generator

**Page:** Selenium Generator

**Steps:**
1. Select a test case from the Test Case Generator
2. Review/edit the selector map if needed
3. Click "Generate Selenium Script"
4. View the generated Python code
5. Download the script

**Generated Script Includes:**
- Complete Selenium imports
- WebDriverWait for robust element waits
- Assertions for expected results
- Error handling with try-except-finally
- Cleanup in finally block
- TODO comments for missing selectors

**Example Output:**

```python
#!/usr/bin/env python3
"""
Selenium Test Script
Test ID: TC-001
Feature: Discount Code
Test Scenario: Apply valid discount code SAVE10
"""

import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "file:///path/to/checkout.html"
TIMEOUT = 10

def test_tc_001():
    driver = None
    try:
        driver = webdriver.Chrome()
        driver.get(BASE_URL)
        wait = WebDriverWait(driver, TIMEOUT)
        
        # Enter discount code
        discount_input = wait.until(EC.presence_of_element_located((By.ID, "discount-code")))
        discount_input.send_keys("SAVE10")
        
        # Click apply button
        apply_btn = driver.find_element(By.ID, "apply-discount-btn")
        apply_btn.click()
        
        # Verify discount applied
        success_msg = wait.until(EC.visibility_of_element_located((By.ID, "discount-success")))
        assert "applied successfully" in success_msg.text.lower()
        
        print("Test TC-001 - PASSED")
        
    except Exception as e:
        print(f"Test TC-001 - FAILED: {e}")
        raise
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    test_tc_001()
```

## 🔌 API Endpoints

### POST `/build_kb`

Build knowledge base from uploaded files.

**Request:**
- Multipart form data with files

**Response:**
```json
{
  "status": "ok",
  "chunks": 42,
  "sources": ["product_specs.md", "ui_ux_guide.txt", "api_endpoints.json"],
  "index_path": "c:\\Users\\...\\faiss_index\\qa_knowledge_base"
}
```

### POST `/generate_testcases`

Generate test cases using RAG.

**Request:**
```json
{
  "query": "Generate positive test cases for discount code feature",
  "top_k": 5
}
```

**Response:**
```json
{
  "status": "ok",
  "test_cases": [...],
  "used_chunks": [...]
}
```

### POST `/generate_selenium`

Generate Selenium script from test case.

**Request:**
```json
{
  "test_case": {
    "Test_ID": "TC-001",
    ...
  }
}
```

**Response:**
```json
{
  "status": "ok",
  "script": "#!/usr/bin/env python3\n...",
  "missing_selectors": []
}
```

### GET `/selectors`

Get current selector map.

**Response:**
```json
{
  "status": "ok",
  "selector_count": 15,
  "selectors": {
    "input_text_discount-code": "#discount-code",
    "button_Apply": "#apply-discount-btn",
    ...
  }
}
```

## 🧪 Testing

Run smoke tests:

```bash
pytest tests/smoke_tests.py -v
```

**Note:** Some tests require `GOOGLE_API_KEY` to be set.

## 📋 Configuration

Edit `backend/settings.py` or set environment variables:

```python
# Google API
GOOGLE_API_KEY = "your_key_here"

# Embedding Model
EMBEDDING_MODEL = "models/embedding-001"

# LLM Model
LLM_MODEL = "gemini-1.5-pro"
LLM_TEMPERATURE = 0.0

# Text Splitting
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

# RAG
RAG_TOP_K = 5
```

## 🎓 How It Works

### Phase 1: Knowledge Base Build

1. **Document Parsing:**
   - PDF → PyMuPDF
   - HTML → BeautifulSoup4
   - JSON → Formatted text
   - MD/TXT → Direct read

2. **Chunking:**
   - RecursiveCharacterTextSplitter
   - Chunk size: 800 characters
   - Overlap: 100 characters

3. **Embedding:**
   - Google's `models/embedding-001`
   - Via LangChain's GoogleGenerativeAIEmbeddings

4. **Vector Store:**
   - FAISS index creation
   - Persist to disk at `faiss_index/`

5. **Selector Extraction:**
   - BeautifulSoup parses HTML
   - Extracts IDs, names, classes
   - Creates selector map

### Phase 2: Test Case Generation (RAG)

1. **Query Processing:**
   - User enters natural language query
   - Embedding created for query

2. **Retrieval:**
   - Similarity search in FAISS
   - Top-k chunks retrieved
   - Chunks formatted with source attribution

3. **Prompt Engineering:**
   - System prompt enforces grounding rules
   - Retrieved chunks wrapped with source markers
   - JSON schema provided for output

4. **LLM Generation:**
   - Gemini 1.5 Pro generates test cases
   - Strict JSON format enforcement
   - No hallucinations - only documented features

5. **Validation:**
   - Pydantic models validate output
   - Check for required fields
   - Verify source references

### Phase 3: Selenium Script Generation

1. **Context Gathering:**
   - Test case details
   - Selector map from HTML
   - Supporting evidence from Grounded_In

2. **Prompt Engineering:**
   - Strict system prompt (senior engineer persona)
   - Only use available selectors
   - Output Python code only
   - Include error handling

3. **LLM Generation:**
   - Gemini generates complete script
   - WebDriverWait for robustness
   - Assertions for validation
   - Cleanup in finally block

4. **Post-Processing:**
   - Remove markdown formatting
   - Add header comments
   - Ensure imports present

## 🔍 Sample Documents

### Product Specifications (product_specs.md)

- Discount code definitions (SAVE10, SAVE20, FREESHIP)
- Validation rules
- Checkout form fields
- Payment methods
- Pricing structure

### UI/UX Guide (ui_ux_guide.txt)

- Layout specifications
- Color scheme
- Form element styling
- Button specifications
- Message formatting
- Interaction flows

### API Endpoints (api_endpoints.json)

- Endpoint definitions
- Request/response schemas
- Validation rules
- Error codes
- Field specifications

## 🎬 Demo

Follow the detailed demo steps in `scripts/demo_recording_steps.txt` to:
- Build knowledge base
- Generate test cases
- Create Selenium scripts
- Use the API directly

## 🛠️ Troubleshooting

### API Key Issues

```bash
# Verify API key is set
echo $GOOGLE_API_KEY  # Linux/Mac
echo %GOOGLE_API_KEY%  # Windows

# Test API connection
python -c "from backend.settings import settings; print(settings.GOOGLE_API_KEY[:10])"
```

### FAISS Index Not Found

```bash
# Rebuild knowledge base
python scripts/build_kb.py
```

### Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Port Already in Use

```bash
# Change port in backend/settings.py
API_PORT = 8001  # Change from 8000

# Or kill existing process
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

## 📚 Key Dependencies

- `fastapi==0.109.0` - Backend API framework
- `streamlit==1.31.0` - Frontend UI
- `langchain==0.1.6` - RAG framework
- `langchain-google-genai==0.0.7` - Google AI integration
- `faiss-cpu==1.7.4` - Vector database
- `google-generativeai==0.3.2` - Google AI SDK
- `beautifulsoup4==4.12.3` - HTML parsing
- `PyMuPDF==1.23.21` - PDF parsing
- `selenium==4.17.2` - Browser automation

## 🤝 Contributing

This is a production-ready scaffold. To extend:

1. Add more document parsers in `backend/parsers.py`
2. Enhance RAG prompts in `backend/rag.py`
3. Add more test case templates
4. Improve selector extraction logic
5. Add support for more programming languages in script generation

## 📄 License

MIT License - Feel free to use and modify.

## 🙏 Acknowledgments

- Google Gemini for powerful LLM capabilities
- LangChain for RAG framework
- FAISS for efficient vector search
- FastAPI and Streamlit for excellent developer experience

## 📞 Support

For issues or questions:
1. Check `scripts/demo_recording_steps.txt` for detailed usage
2. Review logs in backend terminal for errors
3. Verify `.env` configuration
4. Ensure all dependencies installed

---

**Built with ❤️ using Google Gemini, LangChain, and FAISS**
