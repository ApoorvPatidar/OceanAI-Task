"""Pydantic models for request/response validation."""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class BuildKBResponse(BaseModel):
    """Response model for knowledge base build."""
    status: str
    chunks: int
    sources: List[str]
    index_path: str


class GenerateTestCasesRequest(BaseModel):
    """Request model for test case generation."""
    query: str = Field(..., description="RAG query for test case generation")
    top_k: int = Field(default=5, description="Number of chunks to retrieve")


class TestCase(BaseModel):
    """Test case schema."""
    Test_ID: str
    Feature: str
    Test_Scenario: str
    Preconditions: List[str]
    Steps: List[str]
    Expected_Result: str
    Test_Type: Literal["positive", "negative"]
    Grounded_In: List[str]
    SelectorsNeeded: List[str]


class GenerateTestCasesResponse(BaseModel):
    """Response model for test case generation."""
    status: str
    test_cases: List[TestCase]
    used_chunks: List[dict]


class GenerateSeleniumRequest(BaseModel):
    """Request model for Selenium script generation."""
    test_case: TestCase


class GenerateSeleniumResponse(BaseModel):
    """Response model for Selenium script generation."""
    status: str
    script: str
    missing_selectors: List[str]


class ChunkMetadata(BaseModel):
    """Metadata for a document chunk."""
    source: str
    chunk_id: int
    content: str
