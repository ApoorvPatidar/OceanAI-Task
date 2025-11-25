"""FAISS vector store management with persistence."""
from pathlib import Path
from typing import List, Optional
import time
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from backend.settings import settings
from backend.utils import get_logger

logger = get_logger(__name__)


class VectorStoreManager:
    """Manage FAISS vector store with Google embeddings."""
    
    def __init__(self):
        """Initialize vector store manager."""
        self.embeddings = None
        self.vectorstore = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def _initialize_embeddings(self) -> GoogleGenerativeAIEmbeddings:
        """Initialize Google Generative AI embeddings with fallback models."""
        if self.embeddings is None:
            # Try primary model first, then fallback to alternatives
            # Note: embedding-gecko-001 doesn't work with current API version
            embedding_models = [
                settings.EMBEDDING_MODEL,
                "models/text-embedding-004",
                "models/embedding-001",
                "models/gemini-embedding-001"
            ]
            
            for model in embedding_models:
                try:
                    logger.info(f"Initializing embeddings with model: {model}")
                    self.embeddings = GoogleGenerativeAIEmbeddings(
                        model=model,
                        google_api_key=settings.GOOGLE_API_KEY
                    )
                    break
                except Exception as e:
                    logger.warning(f"Failed to initialize {model}: {e}")
                    if model == embedding_models[-1]:  # Last model failed
                        raise
                    continue
                    
        return self.embeddings
    
    def create_vectorstore(self, documents: List[Document]) -> dict:
        """
        Create FAISS vector store from documents with retry logic.
        
        Args:
            documents: List of LangChain Document objects
            
        Returns:
            dict with status, chunk count, sources, and index path
        """
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                # Initialize embeddings
                embeddings = self._initialize_embeddings()
                
                # Split documents into chunks
                logger.info(f"Splitting {len(documents)} documents into chunks")
                chunks = self.text_splitter.split_documents(documents)
                logger.info(f"Created {len(chunks)} chunks")
                
                # Add chunk IDs to metadata
                for i, chunk in enumerate(chunks):
                    chunk.metadata['chunk_id'] = i
                
                # Create FAISS index with retry
                logger.info(f"Creating FAISS index from chunks (attempt {attempt + 1}/{max_retries})")
                self.vectorstore = FAISS.from_documents(
                    documents=chunks,
                    embedding=embeddings
                )
                
                # Persist to disk
                index_path = settings.FAISS_INDEX_DIR / settings.FAISS_INDEX_NAME
                logger.info(f"Persisting FAISS index to {index_path}")
                self.vectorstore.save_local(str(index_path))
                
                # Extract sources
                sources = list(set(doc.metadata.get('source', 'unknown') for doc in documents))
                
                return {
                    "status": "ok",
                    "chunks": len(chunks),
                    "sources": sources,
                    "index_path": str(index_path)
                }
                
            except Exception as e:
                error_msg = str(e)
                is_quota_error = "429" in error_msg or "quota" in error_msg.lower() or "ResourceExhausted" in error_msg
                
                if is_quota_error and attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Quota exceeded, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Error creating vector store: {e}")
                    return {
                        "status": "error",
                        "message": str(e),
                        "chunks": 0,
                        "sources": [],
                        "index_path": ""
                    }
    
    def load_vectorstore(self, index_path: Optional[Path] = None) -> FAISS:
        """
        Load FAISS vector store from disk.
        
        Args:
            index_path: Path to FAISS index (optional)
            
        Returns:
            FAISS vector store
        """
        try:
            if index_path is None:
                index_path = settings.FAISS_INDEX_DIR / settings.FAISS_INDEX_NAME
            
            embeddings = self._initialize_embeddings()
            
            logger.info(f"Loading FAISS index from {index_path}")
            self.vectorstore = FAISS.load_local(
                str(index_path),
                embeddings,
                allow_dangerous_deserialization=True  # Required for FAISS
            )
            
            logger.info("FAISS index loaded successfully")
            return self.vectorstore
            
        except Exception as e:
            logger.error(f"Error loading vector store: {e}")
            raise
    
    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """
        Perform similarity search.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of Document objects
        """
        try:
            if self.vectorstore is None:
                logger.warning("Vector store not loaded, attempting to load")
                self.load_vectorstore()
            
            logger.info(f"Performing similarity search for: {query[:50]}...")
            results = self.vectorstore.similarity_search(query, k=k)
            logger.info(f"Found {len(results)} results")
            
            return results
            
        except Exception as e:
            logger.error(f"Error performing similarity search: {e}")
            raise
    
    def add_documents(self, documents: List[Document]) -> None:
        """
        Add documents to existing vector store.
        
        Args:
            documents: List of Document objects to add
        """
        try:
            if self.vectorstore is None:
                logger.warning("Vector store not loaded, creating new one")
                self.create_vectorstore(documents)
                return
            
            # Split documents
            chunks = self.text_splitter.split_documents(documents)
            
            # Add to existing vectorstore
            logger.info(f"Adding {len(chunks)} chunks to existing vector store")
            self.vectorstore.add_documents(chunks)
            
            # Persist
            index_path = settings.FAISS_INDEX_DIR / settings.FAISS_INDEX_NAME
            self.vectorstore.save_local(str(index_path))
            
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise
    
    def get_chunk_count(self) -> int:
        """Get total number of chunks in vector store."""
        if self.vectorstore is None:
            return 0
        return self.vectorstore.index.ntotal
