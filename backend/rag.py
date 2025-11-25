"""RAG implementation using LangChain and Gemini."""
from typing import List, Dict
import json
import re
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import Document
from langchain.prompts import PromptTemplate
from backend.settings import settings
from backend.vectorstore import VectorStoreManager
from backend.utils import get_logger, format_chunks_for_prompt
from backend.models import TestCase

logger = get_logger(__name__)


# Test Case Generation Prompt Template
TEST_CASE_GENERATION_TEMPLATE = """You are a test case generation assistant. You MUST generate test cases in valid JSON format only.

QUERY: {query}

RETRIEVED DOCUMENTATION:
{retrieved_chunks}

INSTRUCTIONS:
1. Generate test cases based ONLY on the information in the retrieved documentation above
2. If information is missing, use "UNKNOWN" for that field
3. Include both positive and negative test cases
4. Output ONLY a valid JSON array, no additional text or explanation

REQUIRED JSON SCHEMA:
[
  {{
    "Test_ID": "TC-001",
    "Feature": "string",
    "Test_Scenario": "string describing the test",
    "Preconditions": ["list of preconditions"],
    "Steps": ["step 1", "step 2", "..."],
    "Expected_Result": "string describing expected outcome",
    "Test_Type": "positive or negative",
    "Grounded_In": ["source1.md (chunk_0)", "source2.txt (chunk_1)"],
    "SelectorsNeeded": ["selector-name-1", "selector-name-2"]
  }}
]

IMPORTANT:
- Output ONLY the JSON array
- No markdown code blocks
- No explanations before or after the JSON
- Generate at least 3-6 test cases if data supports it
- Reference sources in Grounded_In field

JSON OUTPUT:"""


class RAGEngine:
    """RAG engine for test case generation."""
    
    def __init__(self):
        """Initialize RAG engine."""
        self.vectorstore_manager = VectorStoreManager()
        
        # Initialize LLM with error handling
        try:
            logger.info(f"Initializing LLM with model: {settings.LLM_MODEL}")
            self.llm = ChatGoogleGenerativeAI(
                model=settings.LLM_MODEL,
                temperature=settings.LLM_TEMPERATURE,
                max_output_tokens=settings.LLM_MAX_OUTPUT_TOKENS,
                google_api_key=settings.GOOGLE_API_KEY
            )
        except Exception as e:
            logger.error(f"Failed to initialize LLM with {settings.LLM_MODEL}: {e}")
            # Try fallback model
            fallback_model = "gemini-pro"
            logger.info(f"Trying fallback model: {fallback_model}")
            self.llm = ChatGoogleGenerativeAI(
                model=fallback_model,
                temperature=settings.LLM_TEMPERATURE,
                max_output_tokens=settings.LLM_MAX_OUTPUT_TOKENS,
                google_api_key=settings.GOOGLE_API_KEY
            )
        
        self.prompt_template = PromptTemplate(
            template=TEST_CASE_GENERATION_TEMPLATE,
            input_variables=["query", "retrieved_chunks"]
        )
    
    def load_knowledge_base(self) -> None:
        """Load the FAISS knowledge base."""
        try:
            self.vectorstore_manager.load_vectorstore()
            logger.info("Knowledge base loaded successfully")
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")
            raise
    
    def retrieve_relevant_chunks(self, query: str, top_k: int = 5) -> List[Document]:
        """
        Retrieve relevant chunks for a query.
        
        Args:
            query: User query
            top_k: Number of chunks to retrieve
            
        Returns:
            List of Document objects
        """
        try:
            # Ensure vectorstore is loaded
            if self.vectorstore_manager.vectorstore is None:
                self.load_knowledge_base()
            
            # Retrieve chunks
            chunks = self.vectorstore_manager.similarity_search(query, k=top_k)
            return chunks
            
        except Exception as e:
            logger.error(f"Error retrieving chunks: {e}")
            raise
    
    def generate_test_cases(self, query: str, top_k: int = 5) -> Dict:
        """
        Generate test cases using RAG.
        
        Args:
            query: User query for test case generation
            top_k: Number of chunks to retrieve
            
        Returns:
            Dictionary with test cases and metadata
        """
        try:
            # Retrieve relevant chunks
            logger.info(f"Retrieving chunks for query: {query}")
            chunks = self.retrieve_relevant_chunks(query, top_k)
            
            if not chunks:
                logger.warning("No chunks retrieved")
                return {
                    "status": "error",
                    "message": "No relevant information found in knowledge base",
                    "test_cases": [],
                    "used_chunks": []
                }
            
            # Format chunks for prompt
            formatted_chunks = format_chunks_for_prompt([
                {
                    "page_content": chunk.page_content,
                    "metadata": chunk.metadata
                }
                for chunk in chunks
            ])
            
            # Create prompt
            prompt = self.prompt_template.format(
                query=query,
                retrieved_chunks=formatted_chunks
            )
            
            # Generate test cases
            logger.info("Generating test cases with LLM")
            response = self.llm.invoke(prompt)
            
            # Parse response
            response_text = response.content.strip()
            logger.info(f"LLM Response length: {len(response_text)} characters")
            
            # Check if response is empty
            if not response_text:
                logger.error("LLM returned empty response")
                return {
                    "status": "error",
                    "message": "LLM returned empty response. Please try again or check your API quota.",
                    "test_cases": [],
                    "used_chunks": []
                }
            
            # Extract JSON from response (handle markdown code blocks)
            original_text = response_text
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            # If still empty after extraction, use original
            if not response_text:
                response_text = original_text
            
            # Try to find JSON array or object in the text
            if not response_text.startswith('[') and not response_text.startswith('{'):
                # Look for JSON structure in the text
                import re
                json_match = re.search(r'(\[.*\]|\{.*\})', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(1)
            
            logger.info(f"Extracted JSON length: {len(response_text)} characters")
            
            # Parse JSON
            try:
                test_cases_data = json.loads(response_text)
                
                # Ensure it's a list
                if not isinstance(test_cases_data, list):
                    test_cases_data = [test_cases_data]
                
                # Validate and convert to TestCase models
                test_cases = []
                for tc_data in test_cases_data:
                    try:
                        test_case = TestCase(**tc_data)
                        test_cases.append(test_case)
                    except Exception as e:
                        logger.warning(f"Invalid test case format: {e}")
                        continue
                
                # Prepare used chunks metadata
                used_chunks = [
                    {
                        "source": chunk.metadata.get("source", "unknown"),
                        "chunk_id": chunk.metadata.get("chunk_id", -1),
                        "preview": chunk.page_content[:200] + "..."
                    }
                    for chunk in chunks
                ]
                
                return {
                    "status": "ok",
                    "test_cases": test_cases,
                    "used_chunks": used_chunks
                }
                
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON response: {e}")
                logger.error(f"Response text: {response_text}")
                return {
                    "status": "error",
                    "message": f"Failed to parse LLM response as JSON: {str(e)}",
                    "test_cases": [],
                    "used_chunks": [],
                    "raw_response": response_text
                }
            
        except Exception as e:
            logger.error(f"Error generating test cases: {e}")
            raise
    
    def get_supporting_evidence(self, grounded_in: List[str]) -> str:
        """
        Retrieve supporting evidence based on Grounded_In references.
        
        Args:
            grounded_in: List of source references (e.g., "file.md (chunk_0)")
            
        Returns:
            Formatted evidence string
        """
        # This would ideally retrieve the exact chunks referenced
        # For now, we'll do a best-effort search
        evidence_parts = []
        
        for reference in grounded_in:
            # Extract source name (before parenthesis if present)
            source = reference.split("(")[0].strip()
            
            # Search for content from this source
            try:
                chunks = self.retrieve_relevant_chunks(source, top_k=2)
                for chunk in chunks:
                    if chunk.metadata.get("source") == source:
                        evidence_parts.append(f"=== {reference} ===\n{chunk.page_content}\n=== END ===")
                        break
            except Exception as e:
                logger.warning(f"Could not retrieve evidence for {reference}: {e}")
        
        return "\n\n".join(evidence_parts) if evidence_parts else "No supporting evidence found"
