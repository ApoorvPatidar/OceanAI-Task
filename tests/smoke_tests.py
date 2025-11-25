"""Basic smoke tests for the Autonomous QA Agent."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from backend.settings import settings
from backend.parsers import DocumentParser
from backend.vectorstore import VectorStoreManager
from backend.py_selectors import SelectorExtractor
from backend.models import TestCase


class TestParsers:
    """Test document parsers."""
    
    def test_parse_text_file(self, tmp_path):
        """Test text file parsing."""
        # Create temporary text file
        test_file = tmp_path / "test.txt"
        test_file.write_text("This is a test document.")
        
        content = DocumentParser.parse_text(test_file)
        assert content == "This is a test document."
    
    def test_parse_json_file(self, tmp_path):
        """Test JSON file parsing."""
        import json
        
        test_file = tmp_path / "test.json"
        data = {"key": "value", "number": 42}
        test_file.write_text(json.dumps(data))
        
        content = DocumentParser.parse_json(test_file)
        assert "key: value" in content
        assert "number: 42" in content
    
    def test_files_to_documents(self, tmp_path):
        """Test conversion of files to Document objects."""
        # Create test files
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        documents = DocumentParser.files_to_documents([test_file])
        
        assert len(documents) == 1
        assert documents[0].page_content == "Test content"
        assert documents[0].metadata["source"] == "test.txt"


class TestSelectors:
    """Test selector extraction."""
    
    def test_extract_selectors_from_html(self, tmp_path):
        """Test HTML selector extraction."""
        html_content = """
        <html>
            <body>
                <input type="text" id="email" name="email">
                <button id="submit-btn">Submit</button>
                <div id="message" class="success">Success</div>
            </body>
        </html>
        """
        
        html_file = tmp_path / "test.html"
        html_file.write_text(html_content)
        
        extractor = SelectorExtractor()
        selector_map = extractor.extract_selectors_from_html(html_file)
        
        assert len(selector_map) > 0
        # Check if some expected selectors are present
        assert any("#email" in v for v in selector_map.values())
        assert any("#submit-btn" in v for v in selector_map.values())


class TestModels:
    """Test Pydantic models."""
    
    def test_test_case_model_valid(self):
        """Test TestCase model with valid data."""
        data = {
            "Test_ID": "TC-001",
            "Feature": "Discount Code",
            "Test_Scenario": "Apply valid discount code",
            "Preconditions": ["User is on checkout page"],
            "Steps": ["Enter code SAVE10", "Click Apply"],
            "Expected_Result": "Discount applied",
            "Test_Type": "positive",
            "Grounded_In": ["product_specs.md"],
            "SelectorsNeeded": ["discount-code", "apply-btn"]
        }
        
        test_case = TestCase(**data)
        assert test_case.Test_ID == "TC-001"
        assert test_case.Test_Type == "positive"
    
    def test_test_case_model_invalid_type(self):
        """Test TestCase model with invalid test type."""
        data = {
            "Test_ID": "TC-001",
            "Feature": "Test",
            "Test_Scenario": "Test",
            "Preconditions": [],
            "Steps": [],
            "Expected_Result": "Test",
            "Test_Type": "invalid",  # Should be "positive" or "negative"
            "Grounded_In": [],
            "SelectorsNeeded": []
        }
        
        with pytest.raises(ValueError):
            TestCase(**data)


class TestVectorStore:
    """Test vector store functionality (requires API key)."""
    
    @pytest.mark.skipif(not settings.GOOGLE_API_KEY, reason="GOOGLE_API_KEY not set")
    def test_vectorstore_creation(self, tmp_path):
        """Test FAISS vector store creation."""
        from langchain.schema import Document
        import google.api_core.exceptions
        
        # Create test documents
        documents = [
            Document(page_content="Test content 1", metadata={"source": "test1.txt"}),
            Document(page_content="Test content 2", metadata={"source": "test2.txt"})
        ]
        
        # Override FAISS index directory
        test_index_dir = tmp_path / "faiss_index"
        test_index_dir.mkdir()
        
        original_dir = settings.FAISS_INDEX_DIR
        settings.FAISS_INDEX_DIR = test_index_dir
        
        try:
            manager = VectorStoreManager()
            result = manager.create_vectorstore(documents)
            
            # Check if quota error was returned
            if result["status"] == "error":
                error_msg = result.get("message", "")
                if "429" in error_msg or "quota" in error_msg.lower() or "ResourceExhausted" in error_msg:
                    pytest.skip(f"API quota exceeded - test skipped. Run later when quota resets.")
                else:
                    # Other error - fail the test
                    pytest.fail(f"Unexpected error: {error_msg}")
            
            # If successful, verify results
            assert result["status"] == "ok"
            assert result["chunks"] > 0
            assert len(result["sources"]) == 2
            
        except Exception as e:
            # If quota exceeded, skip test with informative message
            if "429" in str(e) or "quota" in str(e).lower() or "ResourceExhausted" in str(e):
                pytest.skip(f"API quota exceeded - test skipped. Error: {str(e)[:100]}")
            else:
                raise  # Re-raise other exceptions
            
        finally:
            # Restore original directory
            settings.FAISS_INDEX_DIR = original_dir


class TestSettings:
    """Test settings configuration."""
    
    def test_settings_paths_exist(self):
        """Test that configured paths exist."""
        assert settings.BASE_DIR.exists()
        assert settings.ASSETS_DIR.exists()
        assert settings.SUPPORT_DOCS_DIR.exists()
        assert settings.FAISS_INDEX_DIR.exists()
    
    def test_settings_values(self):
        """Test settings default values."""
        assert settings.EMBEDDING_MODEL == "models/text-embedding-004"
        assert settings.LLM_MODEL == "gemini-1.5-pro"
        assert settings.CHUNK_SIZE == 800
        assert settings.CHUNK_OVERLAP == 100


def test_imports():
    """Test that all modules can be imported."""
    try:
        from backend import app
        from backend import models
        from backend import parsers
        from backend import rag
        from backend import py_selectors
        from backend import selenium_gen
        from backend import settings
        from backend import utils
        from backend import vectorstore
        
        assert True
    except ImportError as e:
        pytest.fail(f"Import error: {e}")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
