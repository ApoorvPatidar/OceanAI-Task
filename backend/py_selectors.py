"""HTML selector extraction using BeautifulSoup."""
from pathlib import Path
from typing import Dict, List
from bs4 import BeautifulSoup
from backend.utils import get_logger

logger = get_logger(__name__)


class SelectorExtractor:
    """Extract CSS selectors from HTML."""
    
    @staticmethod
    def extract_selectors_from_html(html_path: Path) -> Dict[str, str]:
        """
        Extract selectors from HTML file.
        Returns a mapping of element descriptions to CSS selectors.
        """
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            soup = BeautifulSoup(html_content, 'lxml')
            selector_map = {}
            
            # Extract elements with IDs
            elements_with_id = soup.find_all(id=True)
            for elem in elements_with_id:
                elem_id = elem.get('id')
                elem_type = elem.name
                text = elem.get_text(strip=True)[:50]  # First 50 chars
                
                key = f"{elem_type}_{elem_id}"
                if text:
                    key += f"_{text[:20]}"
                
                selector_map[key] = f"#{elem_id}"
            
            # Extract form inputs
            inputs = soup.find_all(['input', 'select', 'textarea'])
            for inp in inputs:
                name = inp.get('name', '')
                inp_type = inp.get('type', 'text')
                elem_id = inp.get('id', '')
                
                if elem_id:
                    key = f"input_{inp_type}_{name or elem_id}"
                    selector_map[key] = f"#{elem_id}"
                elif name:
                    key = f"input_{inp_type}_{name}"
                    selector_map[key] = f"[name='{name}']"
            
            # Extract buttons
            buttons = soup.find_all(['button', 'input'])
            for btn in buttons:
                if btn.name == 'input' and btn.get('type') not in ['button', 'submit', 'reset']:
                    continue
                
                text = btn.get_text(strip=True) or btn.get('value', '')
                btn_id = btn.get('id', '')
                btn_class = btn.get('class', [])
                
                if btn_id:
                    key = f"button_{text[:20] or btn_id}"
                    selector_map[key] = f"#{btn_id}"
                elif text:
                    key = f"button_{text[:30]}"
                    selector_map[key] = f"button:contains('{text}')" if btn.name == 'button' else f"input[value='{text}']"
            
            # Extract links
            links = soup.find_all('a', href=True)
            for link in links:
                text = link.get_text(strip=True)
                href = link.get('href')
                link_id = link.get('id', '')
                
                if link_id:
                    key = f"link_{text[:20] or link_id}"
                    selector_map[key] = f"#{link_id}"
                elif text:
                    key = f"link_{text[:30]}"
                    selector_map[key] = f"a:contains('{text}')"
            
            # Extract elements with specific classes
            for class_name in ['error', 'success', 'message', 'alert', 'warning']:
                elements = soup.find_all(class_=lambda x: x and class_name in x.lower() if x else False)
                for elem in elements:
                    classes = ' '.join(elem.get('class', []))
                    key = f"{elem.name}_{class_name}_message"
                    selector_map[key] = f".{classes.split()[0]}"
            
            logger.info(f"Extracted {len(selector_map)} selectors from {html_path}")
            return selector_map
            
        except Exception as e:
            logger.error(f"Error extracting selectors from {html_path}: {e}")
            return {}
    
    @staticmethod
    def format_selector_map(selector_map: Dict[str, str]) -> str:
        """Format selector map for display."""
        if not selector_map:
            return "No selectors found"
        
        lines = ["Selector Map:"]
        for key, selector in sorted(selector_map.items()):
            lines.append(f"  {key}: {selector}")
        
        return "\n".join(lines)
    
    @staticmethod
    def get_selector_for_element(selector_map: Dict[str, str], search_term: str) -> str:
        """Find selector by searching keys."""
        search_lower = search_term.lower()
        
        # Exact match
        if search_term in selector_map:
            return selector_map[search_term]
        
        # Partial match
        for key, selector in selector_map.items():
            if search_lower in key.lower():
                return selector
        
        return ""
