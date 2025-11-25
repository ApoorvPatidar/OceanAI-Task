"""Utility functions for the application."""
import os
import logging
from pathlib import Path
from typing import List
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)


def ensure_dir(path: Path) -> None:
    """Ensure directory exists."""
    path.mkdir(parents=True, exist_ok=True)


def load_json_file(file_path: Path) -> dict:
    """Load JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON file {file_path}: {e}")
        return {}


def save_json_file(data: dict, file_path: Path) -> None:
    """Save data to JSON file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving JSON file {file_path}: {e}")


def format_chunks_for_prompt(chunks: List[dict]) -> str:
    """Format retrieved chunks for prompt with source wrapping."""
    formatted = []
    for i, chunk in enumerate(chunks):
        source = chunk.get('metadata', {}).get('source', 'unknown')
        content = chunk.get('page_content', '')
        
        formatted.append(f"""=== SOURCE: {source} (chunk_{i}) ===
{content}
=== END ===""")
    
    return "\n\n".join(formatted)


def validate_api_key(api_key: str) -> bool:
    """Validate API key format."""
    return bool(api_key and len(api_key) > 10)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage."""
    # Remove or replace unsafe characters
    unsafe_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in unsafe_chars:
        filename = filename.replace(char, '_')
    return filename
