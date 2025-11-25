"""Document parsers for various file formats."""
from pathlib import Path
from typing import List
from bs4 import BeautifulSoup
import fitz  # PyMuPDF
import json
from langchain.schema import Document
from backend.utils import get_logger

logger = get_logger(__name__)


class DocumentParser:
    """Base class for document parsing."""
    
    @staticmethod
    def parse_pdf(file_path: Path) -> str:
        """Parse PDF using PyMuPDF."""
        try:
            doc = fitz.open(file_path)
            text_content = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text_content.append(page.get_text())
            
            doc.close()
            return "\n\n".join(text_content)
        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {e}")
            return ""
    
    @staticmethod
    def parse_html(file_path: Path) -> str:
        """Parse HTML using BeautifulSoup4."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            soup = BeautifulSoup(html_content, 'lxml')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()
            
            # Get text
            text = soup.get_text(separator='\n', strip=True)
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text
        except Exception as e:
            logger.error(f"Error parsing HTML {file_path}: {e}")
            return ""
    
    @staticmethod
    def parse_json(file_path: Path) -> str:
        """Parse JSON and convert to formatted text."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert JSON to readable text format
            def json_to_text(obj, indent=0):
                lines = []
                prefix = "  " * indent
                
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if isinstance(value, (dict, list)):
                            lines.append(f"{prefix}{key}:")
                            lines.append(json_to_text(value, indent + 1))
                        else:
                            lines.append(f"{prefix}{key}: {value}")
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        if isinstance(item, (dict, list)):
                            lines.append(f"{prefix}Item {i + 1}:")
                            lines.append(json_to_text(item, indent + 1))
                        else:
                            lines.append(f"{prefix}- {item}")
                else:
                    lines.append(f"{prefix}{obj}")
                
                return "\n".join(lines)
            
            return json_to_text(data)
        except Exception as e:
            logger.error(f"Error parsing JSON {file_path}: {e}")
            return ""
    
    @staticmethod
    def parse_text(file_path: Path) -> str:
        """Parse plain text files."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error parsing text file {file_path}: {e}")
            return ""
    
    @staticmethod
    def parse_markdown(file_path: Path) -> str:
        """Parse markdown files."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error parsing markdown file {file_path}: {e}")
            return ""
    
    @classmethod
    def parse_file(cls, file_path: Path) -> str:
        """Parse file based on extension."""
        suffix = file_path.suffix.lower()
        
        parsers = {
            '.pdf': cls.parse_pdf,
            '.html': cls.parse_html,
            '.htm': cls.parse_html,
            '.json': cls.parse_json,
            '.txt': cls.parse_text,
            '.md': cls.parse_markdown,
        }
        
        parser = parsers.get(suffix)
        if parser:
            logger.info(f"Parsing {file_path} using {parser.__name__}")
            return parser(file_path)
        else:
            logger.warning(f"No parser for extension {suffix}, treating as text")
            return cls.parse_text(file_path)
    
    @classmethod
    def files_to_documents(cls, file_paths: List[Path]) -> List[Document]:
        """Convert multiple files to LangChain Document objects."""
        documents = []
        
        for file_path in file_paths:
            try:
                content = cls.parse_file(file_path)
                if content.strip():
                    doc = Document(
                        page_content=content,
                        metadata={
                            "source": file_path.name,
                            "full_path": str(file_path),
                            "file_type": file_path.suffix
                        }
                    )
                    documents.append(doc)
                    logger.info(f"Created document from {file_path.name}")
                else:
                    logger.warning(f"Empty content from {file_path.name}")
            except Exception as e:
                logger.error(f"Error converting {file_path} to document: {e}")
        
        return documents
