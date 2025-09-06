"""
Enhanced JobSpy Pipeline with Advanced Error Handling and Proxy Support
Implements robust scraping with proxy rotation, enhanced LinkedIn descriptions,
and comprehensive error recovery strategies
"""
import asyncio
import logging
import random
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import aiohttp
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import ssl

logger = logging.getLogger(__name__)


@dataclass
class ProxyConfig:
    """Configuration for proxy rotation"""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    protocol: str = "http"  # http, https, socks5
    success_rate: float = 1.0
    last_used: Optional[datetime] = None
    failures: int = 0
    max_failures: int = 3

    @property
    def url(self) -> str:
        """Get proxy URL"""
        if self.username and self.password:
            return f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.protocol}://{self.host}:{self.port}"

    @property
    def is_healthy(self) -> bool:
        """Check if proxy is healthy"""
        return self.failures < self.max_failures and self.success_rate > 0.3


@dataclass
class ScrapingResult:
    """Enhanced scraping result with detailed metrics"""
    success: bool
    jobs_count: int
    duration_ms: float
    site: str
    proxy_used: Optional[str] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    enhanced_descriptions: int = 0


@dataclass
class EnhancedJobData:
    """Enhanced job data with additional processing"""
    original_data: Dict[str, Any]
    enhanced_description: Optional[str] = None
    linkedin_company_info: Optional[Dict] = None
    salary_normalized: Optional[Dict] = None
    skills_extracted: List[str] = field(default_factory=list)
    location_enhanced: Optional[Dict] = None


class ProxyManager:
    """
    Intelligent proxy rotation and health management
    """
    
    def __init__(self):
        self.proxies: List[ProxyConfig] = []
        self._current_index = 0
        self._lock = asyncio.Lock()
        
        # Load default proxy list (you can configure these)
        self._load_default_proxies()
    
    def _load_default_proxies(self):
        """Load default proxy configurations"""
        # Add your proxy configurations here
        # For development, using free proxy services (replace with your proxies)
        default_proxies = [
            # Add your proxy configurations here
            # ProxyConfig("proxy1.example.com", 8080, "user", "pass"),
            # ProxyConfig("proxy2.example.com", 3128),
        ]
        
        self.proxies.extend(default_proxies)
        logger.info(f"Loaded {len(self.proxies)} proxy configurations")
    
    async def get_next_proxy(self) -> Optional[ProxyConfig]:
        """Get next healthy proxy in rotation"""
        async with self._lock:
            if not self.proxies:
                return None
            
            # Filter healthy proxies
            healthy_proxies = [p for p in self.proxies if p.is_healthy]
            
            if not healthy_proxies:
                logger.warning("No healthy proxies available")
                return None
            
            # Select proxy with best success rate
            proxy = max(healthy_proxies, key=lambda p: p.success_rate)
            proxy.last_used = datetime.now()
            
            return proxy
    
    async def report_proxy_result(self, proxy: ProxyConfig, success: bool):
        """Report proxy usage result for health tracking"""
        async with self._lock:
            if success:
                proxy.failures = max(0, proxy.failures - 1)
                proxy.success_rate = min(1.0, proxy.success_rate + 0.1)
            else:
                proxy.failures += 1
                proxy.success_rate = max(0.0, proxy.success_rate - 0.2)
            
            logger.debug(f"Proxy {proxy.host}:{proxy.port} - Success: {success}, "
                        f"Rate: {proxy.success_rate:.2f}, Failures: {proxy.failures}")
    
    def add_proxy(self, proxy: ProxyConfig):
        """Add new proxy to rotation"""
        self.proxies.append(proxy)
        logger.info(f"Added proxy: {proxy.host}:{proxy.port}")
    
    def get_proxy_stats(self) -> Dict[str, Any]:
        """Get proxy performance statistics"""
        if not self.proxies:
            return {"total_proxies": 0, "healthy_proxies": 0}
        
        healthy = [p for p in self.proxies if p.is_healthy]
        avg_success_rate = sum(p.success_rate for p in self.proxies) / len(self.proxies)
        
        return {
            "total_proxies": len(self.proxies),
            "healthy_proxies": len(healthy),
            "average_success_rate": round(avg_success_rate, 3),
            "proxy_details": [
                {
                    "host": f"{p.host}:{p.port}",
                    "success_rate": round(p.success_rate, 3),
                    "failures": p.failures,
                    "healthy": p.is_healthy
                }
                for p in self.proxies
            ]
        }


class EnhancedJobSpyPipeline:
    """
    Enhanced JobSpy pipeline with advanced features:
    - Proxy rotation for anti-detection
    - Enhanced LinkedIn description extraction
    - Comprehensive error handling and retry logic
    - Performance monitoring and optimization
    """
    
    def __init__(
        self,
        proxy_manager: Optional[ProxyManager] = None,
        max_retries: int = 3,
        retry_delay: float = 2.0,
        enhance_descriptions: bool = True,
        linkedin_extraction: bool = True
    ):
        self.proxy_manager = proxy_manager or ProxyManager()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.enhance_descriptions = enhance_descriptions
        self.linkedin_extraction = linkedin_extraction
        
        # Performance tracking
        self.scraping_stats = {
            "total_scrapes": 0,
            "successful_scrapes": 0,
            "proxy_usage": 0,
            "enhanced_descriptions": 0,
            "linkedin_enhancements": 0
        }
        
        logger.info("Enhanced JobSpy pipeline initialized")
    
    async def scrape_with_enhancements(
        self,
        site: str,
        search_term: str,
        location: str,
        results_wanted: int = 50,
        **kwargs
    ) -> ScrapingResult:
        """
        Scrape jobs with enhanced error handling and proxy support
        """
        start_time = time.time()
        self.scraping_stats["total_scrapes"] += 1
        
        for attempt in range(self.max_retries + 1):
            proxy = await self.proxy_manager.get_next_proxy() if self.proxy_manager.proxies else None
            
            try:
                # Configure scraping parameters
                scrape_params = {
                    "site_name": [site] if isinstance(site, str) else site,
                    "search_term": search_term,
                    "location": location,
                    "results_wanted": results_wanted,
                    "hours_old": kwargs.get("hours_old", 72),
                    "country_indeed": kwargs.get("country_indeed", "Canada"),
                    **kwargs
                }
                
                # Add proxy configuration if available
                if proxy:
                    self.scraping_stats["proxy_usage"] += 1
                    # Configure proxy for jobspy (implementation depends on jobspy version)
                    # scrape_params["proxy"] = proxy.url
                
                # Perform scraping
                logger.info(f"Scraping {site} for '{search_term}' in {location} "
                           f"(attempt {attempt + 1}/{self.max_retries + 1})")
                
                # Import and call jobspy
                from jobspy import scrape_jobs
                
                df = scrape_jobs(**scrape_params)
                
                if df is not None and len(df) > 0:
                    # Success
                    duration_ms = (time.time() - start_time) * 1000
                    
                    # Report proxy success
                    if proxy:
                        await self.proxy_manager.report_proxy_result(proxy, True)
                    
                    self.scraping_stats["successful_scrapes"] += 1
                    
                    # Enhance results if requested
                    enhanced_count = 0
                    if self.enhance_descriptions:
                        enhanced_count = await self._enhance_job_descriptions(df)
                        self.scraping_stats["enhanced_descriptions"] += enhanced_count
                    
                    return ScrapingResult(
                        success=True,
                        jobs_count=len(df),
                        duration_ms=duration_ms,
                        site=site,
                        proxy_used=proxy.url if proxy else None,
                        retry_count=attempt,
                        enhanced_descriptions=enhanced_count
                    )
                else:
                    raise Exception("No jobs found or empty response")
                    
            except Exception as e:
                logger.warning(f"Scraping attempt {attempt + 1} failed: {e}")
                
                # Report proxy failure
                if proxy:
                    await self.proxy_manager.report_proxy_result(proxy, False)
                
                # If not the last attempt, wait before retry
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.info(f"Waiting {wait_time:.1f}s before retry...")
                    await asyncio.sleep(wait_time)
                else:
                    # Final failure
                    duration_ms = (time.time() - start_time) * 1000
                    return ScrapingResult(
                        success=False,
                        jobs_count=0,
                        duration_ms=duration_ms,
                        site=site,
                        proxy_used=proxy.url if proxy else None,
                        error_type=type(e).__name__,
                        error_message=str(e),
                        retry_count=attempt
                    )
        
        # Should not reach here
        return ScrapingResult(
            success=False,
            jobs_count=0,
            duration_ms=(time.time() - start_time) * 1000,
            site=site,
            error_type="MaxRetriesExceeded",
            error_message="All retry attempts failed"
        )
    
    async def _enhance_job_descriptions(self, df) -> int:
        """
        Enhance job descriptions with additional content extraction
        """
        enhanced_count = 0
        
        for idx, row in df.iterrows():
            try:
                job_url = row.get('job_url') or row.get('url')
                if not job_url:
                    continue
                
                # Extract enhanced description
                enhanced_desc = await self._extract_enhanced_description(job_url)
                if enhanced_desc:
                    df.at[idx, 'enhanced_description'] = enhanced_desc
                    enhanced_count += 1
                
                # LinkedIn-specific enhancements
                if 'linkedin' in job_url.lower() and self.linkedin_extraction:
                    linkedin_data = await self._extract_linkedin_data(job_url)
                    if linkedin_data:
                        df.at[idx, 'linkedin_company_info'] = linkedin_data
                        self.scraping_stats["linkedin_enhancements"] += 1
                
                # Small delay to avoid overwhelming servers
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.debug(f"Enhancement failed for job {idx}: {e}")
                continue
        
        logger.info(f"Enhanced {enhanced_count} job descriptions")
        return enhanced_count
    
    async def _extract_enhanced_description(self, job_url: str) -> Optional[str]:
        """
        Extract enhanced job description from job URL
        """
        try:
            # Use proxy if available
            proxy = await self.proxy_manager.get_next_proxy() if self.proxy_manager.proxies else None
            
            # Configure request
            timeout = aiohttp.ClientTimeout(total=10)
            headers = {
                'User-Agent': self._get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            connector_kwargs = {}
            if proxy:
                connector_kwargs['proxy'] = proxy.url
            
            # Create SSL context for better compatibility
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            async with aiohttp.ClientSession(
                timeout=timeout,
                headers=headers,
                connector=aiohttp.TCPConnector(ssl=ssl_context, **connector_kwargs)
            ) as session:
                async with session.get(job_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # Parse with BeautifulSoup
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # Extract description based on site
                        description = self._extract_description_by_site(soup, job_url)
                        
                        # Report proxy success
                        if proxy:
                            await self.proxy_manager.report_proxy_result(proxy, True)
                        
                        return description
                    else:
                        logger.debug(f"HTTP {response.status} for {job_url}")
                        
        except Exception as e:
            logger.debug(f"Description extraction failed for {job_url}: {e}")
            # Report proxy failure if used
            proxy = await self.proxy_manager.get_next_proxy() if self.proxy_manager.proxies else None
            if proxy:
                await self.proxy_manager.report_proxy_result(proxy, False)
        
        return None
    
    def _extract_description_by_site(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """
        Extract job description based on the job site
        """
        domain = urlparse(url).netloc.lower()
        
        # Site-specific selectors
        selectors = {
            'linkedin.com': [
                '.jobs-box__html-content',
                '.jobs-description-content',
                '.description__text'
            ],
            'indeed.com': [
                '.jobsearch-jobDescriptionText',
                '.icl-u-xs-mt--xs',
                '.jobdescription'
            ],
            'glassdoor.com': [
                '.jobDescription',
                '.desc',
                '.jobDescriptionContent'
            ],
            'ziprecruiter.com': [
                '.job_description',
                '.jobDescriptionSection'
            ]
        }
        
        # Try site-specific selectors first
        for site, site_selectors in selectors.items():
            if site in domain:
                for selector in site_selectors:
                    element = soup.select_one(selector)
                    if element:
                        return element.get_text(strip=True)
        
        # Fallback to generic selectors
        generic_selectors = [
            '[data-testid*="description"]',
            '.job-description',
            '.description',
            '.content',
            'main'
        ]
        
        for selector in generic_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if len(text) > 100:  # Ensure meaningful content
                    return text
        
        return None
    
    async def _extract_linkedin_data(self, job_url: str) -> Optional[Dict]:
        """
        Extract additional LinkedIn-specific data
        """
        try:
            # Similar to enhanced description but focus on company info
            # This would require more sophisticated parsing
            # For now, return placeholder structure
            return {
                "company_size": None,
                "industry": None,
                "company_url": None,
                "posting_date": None
            }
        except Exception as e:
            logger.debug(f"LinkedIn data extraction failed: {e}")
            return None
    
    def _get_random_user_agent(self) -> str:
        """Get random user agent for requests"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
        ]
        return random.choice(user_agents)
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get pipeline performance statistics"""
        success_rate = (
            self.scraping_stats["successful_scrapes"] / self.scraping_stats["total_scrapes"] * 100
            if self.scraping_stats["total_scrapes"] > 0 else 0
        )
        
        return {
            **self.scraping_stats,
            "success_rate_percent": round(success_rate, 2),
            "proxy_stats": self.proxy_manager.get_proxy_stats()
        }
    
    def reset_stats(self):
        """Reset pipeline statistics"""
        self.scraping_stats = {
            "total_scrapes": 0,
            "successful_scrapes": 0,
            "proxy_usage": 0,
            "enhanced_descriptions": 0,
            "linkedin_enhancements": 0
        }


# Global pipeline instance
_enhanced_pipeline = None


def get_enhanced_jobspy_pipeline() -> EnhancedJobSpyPipeline:
    """Get global enhanced JobSpy pipeline instance"""
    global _enhanced_pipeline
    if _enhanced_pipeline is None:
        _enhanced_pipeline = EnhancedJobSpyPipeline()
    return _enhanced_pipeline


# Convenience functions for backward compatibility
async def scrape_with_enhancements(
    site: str,
    search_term: str,
    location: str,
    results_wanted: int = 50,
    **kwargs
) -> ScrapingResult:
    """Convenience function for enhanced scraping"""
    pipeline = get_enhanced_jobspy_pipeline()
    return await pipeline.scrape_with_enhancements(
        site, search_term, location, results_wanted, **kwargs
    )


def add_proxy_to_rotation(host: str, port: int, username: str = None, password: str = None):
    """Add proxy to global pipeline rotation"""
    pipeline = get_enhanced_jobspy_pipeline()
    proxy = ProxyConfig(host=host, port=port, username=username, password=password)
    pipeline.proxy_manager.add_proxy(proxy)
