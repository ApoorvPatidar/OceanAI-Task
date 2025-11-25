"""FastAPI application with three main endpoints."""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pathlib import Path
import shutil
import tempfile

from backend.settings import settings
from backend.models import (
    BuildKBResponse,
    GenerateTestCasesRequest,
    GenerateTestCasesResponse,
    GenerateSeleniumRequest,
    GenerateSeleniumResponse
)
from backend.parsers import DocumentParser
from backend.vectorstore import VectorStoreManager
from backend.rag import RAGEngine
from backend.selenium_gen import SeleniumScriptGenerator
from backend.py_selectors import SelectorExtractor
from backend.utils import get_logger, sanitize_filename

logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="Autonomous QA Agent API for test case and Selenium script generation"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
vectorstore_manager = VectorStoreManager()
rag_engine = RAGEngine()
selenium_generator = SeleniumScriptGenerator()
selector_extractor = SelectorExtractor()

# Storage for checkout.html path and selectors
checkout_html_path = None
global_selector_map = {}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Autonomous QA Agent API",
        "version": settings.API_VERSION,
        "endpoints": {
            "build_kb": "/build_kb",
            "generate_testcases": "/generate_testcases",
            "generate_selenium": "/generate_selenium"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "vectorstore_loaded": vectorstore_manager.vectorstore is not None,
        "api_key_configured": bool(settings.GOOGLE_API_KEY)
    }


@app.post("/build_kb", response_model=BuildKBResponse)
async def build_knowledge_base(files: List[UploadFile] = File(...)):
    """
    Build knowledge base from uploaded documents.
    
    Accepts multiple files including:
    - Support documents (md, txt, json, pdf)
    - checkout.html
    
    Returns:
        BuildKBResponse with status, chunk count, sources, and index path
    """
    global checkout_html_path, global_selector_map
    
    try:
        logger.info(f"Received {len(files)} files for knowledge base build")
        
        # Create temporary directory for uploaded files
        temp_dir = Path(tempfile.mkdtemp())
        file_paths = []
        
        # Save uploaded files
        for upload_file in files:
            # Sanitize filename
            safe_filename = sanitize_filename(upload_file.filename)
            file_path = temp_dir / safe_filename
            
            # Save file
            with open(file_path, "wb") as f:
                content = await upload_file.read()
                f.write(content)
            
            logger.info(f"Saved file: {safe_filename}")
            
            # Check if it's checkout.html
            if safe_filename.lower() == "checkout.html" or "checkout" in safe_filename.lower():
                # Copy to assets directory
                checkout_dest = settings.ASSETS_DIR / "checkout.html"
                shutil.copy(file_path, checkout_dest)
                checkout_html_path = checkout_dest
                
                # Extract selectors
                logger.info("Extracting selectors from checkout.html")
                global_selector_map = selector_extractor.extract_selectors_from_html(checkout_dest)
                logger.info(f"Extracted {len(global_selector_map)} selectors")
            else:
                # Add to file list for vector store
                file_paths.append(file_path)
        
        if not file_paths:
            raise HTTPException(
                status_code=400,
                detail="No support documents provided. Please upload at least one document."
            )
        
        # Parse documents
        logger.info(f"Parsing {len(file_paths)} documents")
        documents = DocumentParser.files_to_documents(file_paths)
        
        if not documents:
            raise HTTPException(
                status_code=400,
                detail="No valid documents could be parsed"
            )
        
        # Create vector store
        logger.info("Creating FAISS vector store")
        result = vectorstore_manager.create_vectorstore(documents)
        
        # Clean up temp directory
        shutil.rmtree(temp_dir)
        
        logger.info("Knowledge base built successfully")
        return BuildKBResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error building knowledge base: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate_testcases", response_model=GenerateTestCasesResponse)
async def generate_test_cases(request: GenerateTestCasesRequest):
    """
    Generate test cases using RAG.
    
    Args:
        request: GenerateTestCasesRequest with query and top_k
        
    Returns:
        GenerateTestCasesResponse with test cases and used chunks
    """
    try:
        logger.info(f"Generating test cases for query: {request.query}")
        
        # Ensure knowledge base is loaded
        if rag_engine.vectorstore_manager.vectorstore is None:
            try:
                rag_engine.load_knowledge_base()
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Knowledge base not available. Please build it first. Error: {str(e)}"
                )
        
        # Generate test cases
        result = rag_engine.generate_test_cases(
            query=request.query,
            top_k=request.top_k
        )
        
        if result["status"] == "error":
            raise HTTPException(
                status_code=500,
                detail=result.get("message", "Error generating test cases")
            )
        
        return GenerateTestCasesResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating test cases: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate_selenium", response_model=GenerateSeleniumResponse)
async def generate_selenium_script(request: GenerateSeleniumRequest):
    """
    Generate Selenium script from test case.
    
    Args:
        request: GenerateSeleniumRequest with test_case
        
    Returns:
        GenerateSeleniumResponse with script and missing selectors
    """
    try:
        logger.info(f"Generating Selenium script for test case: {request.test_case.Test_ID}")
        
        # Use global selector map or empty dict
        selector_map = global_selector_map if global_selector_map else {}
        
        if not selector_map:
            logger.warning("No selector map available. Script may be incomplete.")
        
        # Get supporting evidence from Grounded_In
        support_evidence = ""
        if request.test_case.Grounded_In:
            try:
                # Ensure RAG engine is loaded
                if rag_engine.vectorstore_manager.vectorstore is None:
                    rag_engine.load_knowledge_base()
                
                support_evidence = rag_engine.get_supporting_evidence(
                    request.test_case.Grounded_In
                )
            except Exception as e:
                logger.warning(f"Could not retrieve supporting evidence: {e}")
        
        # Generate script
        result = selenium_generator.generate_script(
            test_case=request.test_case,
            selector_map=selector_map,
            support_evidence=support_evidence
        )
        
        return GenerateSeleniumResponse(**result)
        
    except Exception as e:
        logger.error(f"Error generating Selenium script: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/selectors")
async def get_selectors():
    """
    Get the current selector map.
    
    Returns:
        Dictionary of selectors
    """
    return {
        "status": "ok",
        "selector_count": len(global_selector_map),
        "selectors": global_selector_map
    }


if __name__ == "__main__":
    import uvicorn
    
    # Check API key
    if not settings.GOOGLE_API_KEY:
        logger.warning("GOOGLE_API_KEY not set. Please set it in .env file.")
    
    logger.info(f"Starting server on {settings.API_HOST}:{settings.API_PORT}")
    uvicorn.run(
        "app:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
