"""
Playwright MCP Browser Client
Provides a wrapper for interacting with the Playwright MCP server for job scraping.
"""

import asyncio
import json
from typing import Optional, List, Dict, Any
from datetime import datetime

# Import MCP tools that are available
try:
    from mcp_playwright_browser_navigate import mcp_playwright_browser_navigate
    from mcp_playwright_browser_snapshot import mcp_playwright_browser_snapshot
    from mcp_playwright_browser_click import mcp_playwright_browser_click
    from mcp_playwright_browser_type import mcp_playwright_browser_type
    from mcp_playwright_browser_wait_for import mcp_playwright_browser_wait_for
    MCP_AVAILABLE = True
except ImportError:
    print("Warning: MCP Playwright tools not available. Falling back to standard Playwright.")
    MCP_AVAILABLE = False


class MCPBrowserClient:
    """Client for interacting with Playwright MCP server for job scraping."""
    
    def __init__(self):
        self.mcp_available = MCP_AVAILABLE
        self._current_page_content = None
        
    async def navigate_to_url(self, url: str) -> bool:
        """Navigate to a URL using MCP."""
        if not self.mcp_available:
            return False
            
        try:
            result = await mcp_playwright_browser_navigate(url=url)
            return True
        except Exception as e:
            print(f"MCP Navigation error: {e}")
            return False
    
    async def get_page_snapshot(self) -> Optional[Dict]:
        """Get accessibility snapshot of current page."""
        if not self.mcp_available:
            return None
            
        try:
            snapshot = await mcp_playwright_browser_snapshot()
            self._current_page_content = snapshot
            return snapshot
        except Exception as e:
            print(f"MCP Snapshot error: {e}")
            return None
    
    async def find_job_elements(self, snapshot: Dict) -> List[Dict]:
        """Extract job elements from accessibility snapshot."""
        job_elements = []
        
        if not snapshot:
            return job_elements
            
        # Look for job-related elements in the accessibility tree
        # This is a simplified example - you'd need to adapt based on actual site structure
        def traverse_tree(node, path=""):
            if isinstance(node, dict):
                # Look for job container elements
                if self._is_job_element(node):
                    job_elements.append({
                        'node': node,
                        'path': path,
                        'ref': node.get('ref', f"job_{len(job_elements)}")
                    })
                
                # Recursively traverse children
                for key, child in node.items():
                    if key == 'children' and isinstance(child, list):
                        for i, child_node in enumerate(child):
                            traverse_tree(child_node, f"{path}/{key}[{i}]")
                    elif isinstance(child, (dict, list)):
                        traverse_tree(child, f"{path}/{key}")
        
        traverse_tree(snapshot)
        return job_elements
    
    def _is_job_element(self, node: Dict) -> bool:
        """Check if a node represents a job listing element."""
        if not isinstance(node, dict):
            return False
            
        # Look for common job listing indicators
        node_text = str(node.get('text', '')).lower()
        node_role = str(node.get('role', '')).lower()
        node_class = str(node.get('className', '')).lower()
        
        job_indicators = [
            'job', 'position', 'role', 'opening', 'career',
            'organic-job', 'job-listing', 'job-card'
        ]
        
        return any(indicator in node_text or indicator in node_class for indicator in job_indicators)
    
    async def extract_job_data_from_element(self, job_element: Dict, keyword: str, page_num: int, job_num: int) -> Optional[Dict]:
        """Extract job data from a job element."""
        try:
            node = job_element.get('node', {})
            text_content = node.get('text', '')
            
            if not text_content:
                return None
                
            lines = [line.strip() for line in text_content.split('\n') if line.strip()]
            
            if len(lines) < 2:
                return None
            
            job_data = {
                'title': lines[0],
                'company': lines[1],
                'location': lines[2] if len(lines) > 2 else "",
                'summary': " ".join(lines[3:]) if len(lines) > 3 else "",
                'search_keyword': keyword,
                'job_id': f"{keyword}_{page_num}_{job_num}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'url': node.get('href', ''),
                'raw_element': node
            }
            
            return job_data
            
        except Exception as e:
            print(f"Error extracting job data: {e}")
            return None
    
    async def wait_for_content(self, text: str = None, timeout: int = 5000) -> bool:
        """Wait for specific content to appear on page."""
        if not self.mcp_available:
            return True
            
        try:
            if text:
                await mcp_playwright_browser_wait_for(text=text, time=timeout/1000)
            else:
                await mcp_playwright_browser_wait_for(time=timeout/1000)
            return True
        except Exception as e:
            print(f"MCP Wait error: {e}")
            return False


# Fallback functions for when MCP is not available
class FallbackBrowserClient:
    """Fallback client when MCP is not available."""
    
    def __init__(self):
        self.mcp_available = False
    
    async def navigate_to_url(self, url: str) -> bool:
        print(f"Fallback: Would navigate to {url}")
        return False
    
    async def get_page_snapshot(self) -> Optional[Dict]:
        print("Fallback: Would get page snapshot")
        return None
    
    async def find_job_elements(self, snapshot: Dict) -> List[Dict]:
        print("Fallback: Would find job elements")
        return []
    
    async def extract_job_data_from_element(self, job_element: Dict, keyword: str, page_num: int, job_num: int) -> Optional[Dict]:
        print("Fallback: Would extract job data")
        return None
    
    async def wait_for_content(self, text: str = None, timeout: int = 5000) -> bool:
        print("Fallback: Would wait for content")
        return True


def get_browser_client() -> MCPBrowserClient:
    """Get the appropriate browser client (MCP or fallback)."""
    if MCP_AVAILABLE:
        return MCPBrowserClient()
    else:
        return FallbackBrowserClient()
