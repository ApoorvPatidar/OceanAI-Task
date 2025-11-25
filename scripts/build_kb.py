#!/usr/bin/env python3
"""
Script to build knowledge base from support documents.
Can be run independently or called from the API.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.settings import settings
from backend.parsers import DocumentParser
from backend.vectorstore import VectorStoreManager
from backend.py_selectors import SelectorExtractor
from backend.utils import get_logger

logger = get_logger(__name__)


def build_knowledge_base():
    """Build knowledge base from files in assets directory."""
    
    logger.info("=" * 60)
    logger.info("BUILDING KNOWLEDGE BASE")
    logger.info("=" * 60)
    
    # Check if support docs directory exists
    if not settings.SUPPORT_DOCS_DIR.exists():
        logger.error(f"Support docs directory not found: {settings.SUPPORT_DOCS_DIR}")
        return False
    
    # Collect all support documents
    file_paths = []
    for ext in ['*.md', '*.txt', '*.json', '*.pdf']:
        file_paths.extend(settings.SUPPORT_DOCS_DIR.glob(ext))
    
    if not file_paths:
        logger.warning("No support documents found")
        return False
    
    logger.info(f"Found {len(file_paths)} support documents:")
    for fp in file_paths:
        logger.info(f"  - {fp.name}")
    
    # Parse documents
    logger.info("\nParsing documents...")
    documents = DocumentParser.files_to_documents(file_paths)
    
    if not documents:
        logger.error("No valid documents could be parsed")
        return False
    
    logger.info(f"Successfully parsed {len(documents)} documents")
    
    # Create vector store
    logger.info("\nCreating FAISS vector store...")
    vectorstore_manager = VectorStoreManager()
    
    try:
        result = vectorstore_manager.create_vectorstore(documents)
        
        logger.info("\n" + "=" * 60)
        logger.info("KNOWLEDGE BASE BUILT SUCCESSFULLY")
        logger.info("=" * 60)
        logger.info(f"Chunks created: {result['chunks']}")
        logger.info(f"Index path: {result['index_path']}")
        logger.info("\nSources:")
        for source in result['sources']:
            logger.info(f"  - {source}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating vector store: {e}")
        return False


def extract_selectors():
    """Extract selectors from checkout.html."""
    
    logger.info("\n" + "=" * 60)
    logger.info("EXTRACTING SELECTORS FROM CHECKOUT.HTML")
    logger.info("=" * 60)
    
    checkout_path = settings.ASSETS_DIR / "checkout.html"
    
    if not checkout_path.exists():
        logger.warning(f"checkout.html not found at {checkout_path}")
        return {}
    
    selector_extractor = SelectorExtractor()
    selector_map = selector_extractor.extract_selectors_from_html(checkout_path)
    
    logger.info(f"\nExtracted {len(selector_map)} selectors:")
    logger.info(selector_extractor.format_selector_map(selector_map))
    
    return selector_map


def main():
    """Main execution."""
    
    # Check API key
    if not settings.GOOGLE_API_KEY:
        logger.warning("\n" + "!" * 60)
        logger.warning("WARNING: GOOGLE_API_KEY not set!")
        logger.warning("Please set it in .env file before using the API")
        logger.warning("!" * 60 + "\n")
    
    # Build knowledge base
    success = build_knowledge_base()
    
    # Extract selectors
    if (settings.ASSETS_DIR / "checkout.html").exists():
        extract_selectors()
    
    if success:
        logger.info("\n" + "=" * 60)
        logger.info("SETUP COMPLETE")
        logger.info("=" * 60)
        logger.info("\nYou can now:")
        logger.info("1. Start the FastAPI backend: python backend/app.py")
        logger.info("2. Start the Streamlit frontend: streamlit run frontend/streamlit_app.py")
        logger.info("=" * 60)
        return 0
    else:
        logger.error("\nSetup failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
