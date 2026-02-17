"""
Scraper Interfaces and Implementations

Following SOLID principles with Protocol pattern and dependency injection.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Protocol
from dataclasses import dataclass
from playwright.async_api import async_playwright, Browser, Page
from bs4 import BeautifulSoup
import asyncio

from app.config import settings


# ============================================
# Data Models
# ============================================

@dataclass
class ExtractionRule:
    """
    Rule for extracting data from HTML.
    
    Attributes:
        selector: CSS selector
        attribute: HTML attribute to extract (None for text content)
        multiple: Whether to extract all matches or just first
    """
    selector: str
    attribute: Optional[str] = None
    multiple: bool = False


@dataclass
class ScrapedData:
    """
    Result of a scraping operation.
    
    Attributes:
        url: Source URL
        title: Page title
        data: Extracted data
        metadata: Additional metadata
        success: Whether scraping was successful
        error: Error message if failed
    """
    url: str
    title: Optional[str] = None
    data: Dict = None
    metadata: Dict = None
    success: bool = True
    error: Optional[str] = None


# ============================================
# Protocols (Interfaces)
# ============================================

class BrowserProvider(Protocol):
    """
    Protocol for browser automation providers.
    
    Allows swapping between Playwright, Selenium, etc.
    """
    
    async def fetch_page(self, url: str) -> str:
        """Fetch page HTML"""
        ...
    
    async def close(self) -> None:
        """Close browser"""
        ...


class HTMLParser(Protocol):
    """
    Protocol for HTML parsing.
    
    Allows swapping between BeautifulSoup, lxml, etc.
    """
    
    def parse(self, html: str) -> object:
        """Parse HTML string"""
        ...
    
    def extract(self, parsed_html: object, rule: ExtractionRule) -> any:
        """Extract data using rule"""
        ...


class CacheProvider(Protocol):
    """
    Protocol for caching scraped data.
    """
    
    async def get(self, key: str) -> Optional[str]:
        """Get cached value"""
        ...
    
    async def set(self, key: str, value: str, ttl: int) -> None:
        """Set cached value with TTL"""
        ...


# ============================================
# Browser Provider Implementation
# ============================================

class PlaywrightBrowserProvider:
    """
    Playwright implementation of BrowserProvider.
    
    Handles JavaScript rendering and dynamic content.
    """
    
    def __init__(
        self,
        headless: bool = None,
        timeout: int = None,
        user_agent: str = None
    ):
        """
        Initialize Playwright browser.
        
        Args:
            headless: Run in headless mode
            timeout: Page load timeout in milliseconds
            user_agent: Custom user agent
        """
        self.headless = headless if headless is not None else settings.headless
        self.timeout = timeout or settings.timeout
        self.user_agent = user_agent or settings.user_agent
        
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._page: Optional[Page] = None
    
    async def _ensure_browser(self):
        """Lazy browser initialization"""
        if self._browser is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless
            )
    
    async def fetch_page(self, url: str) -> str:
        """
        Fetch page HTML with JavaScript rendering.
        
        Args:
            url: URL to fetch
            
        Returns:
            Rendered HTML content
            
        Raises:
            Exception: If page fetch fails
        """
        await self._ensure_browser()
        
        try:
            self._page = await self._browser.new_page(
                user_agent=self.user_agent
            )
            
            await self._page.goto(url, timeout=self.timeout)
            await self._page.wait_for_load_state("networkidle")
            
            html = await self._page.content()
            await self._page.close()
            
            return html
        
        except Exception as e:
            if self._page:
                await self._page.close()
            raise Exception(f"Failed to fetch page: {str(e)}")
    
    async def close(self) -> None:
        """Close browser and cleanup"""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()


# ============================================
# HTML Parser Implementation
# ============================================

class BeautifulSoupParser:
    """
    BeautifulSoup implementation of HTMLParser.
    
    Parses and extracts data from HTML.
    """
    
    def parse(self, html: str) -> BeautifulSoup:
        """
        Parse HTML string.
        
        Args:
            html: HTML content
            
        Returns:
            BeautifulSoup object
        """
        return BeautifulSoup(html, 'lxml')
    
    def extract(self, parsed_html: BeautifulSoup, rule: ExtractionRule) -> any:
        """
        Extract data using extraction rule.
        
        Args:
            parsed_html: Parsed HTML object
            rule: Extraction rule
            
        Returns:
            Extracted data (string, list, or None)
        """
        if rule.multiple:
            elements = parsed_html.select(rule.selector)
            if rule.attribute:
                return [elem.get(rule.attribute) for elem in elements]
            else:
                return [elem.get_text(strip=True) for elem in elements]
        else:
            element = parsed_html.select_one(rule.selector)
            if element:
                if rule.attribute:
                    return element.get(rule.attribute)
                else:
                    return element.get_text(strip=True)
            return None


# ============================================
# Cache Implementation
# ============================================

class InMemoryCache:
    """
    Simple in-memory cache implementation.
    
    For production, replace with Redis implementation.
    """
    
    def __init__(self):
        self._cache: Dict[str, tuple] = {}
    
    async def get(self, key: str) -> Optional[str]:
        """Get cached value if not expired"""
        if key in self._cache:
            value, expiry = self._cache[key]
            if asyncio.get_event_loop().time() < expiry:
                return value
            else:
                del self._cache[key]
        return None
    
    async def set(self, key: str, value: str, ttl: int) -> None:
        """Set value with TTL"""
        expiry = asyncio.get_event_loop().time() + ttl
        self._cache[key] = (value, expiry)


# ============================================
# Scraper Service
# ============================================

class ScraperService:
    """
    High-level scraper service with dependency injection.
    
    Orchestrates browser automation, HTML parsing, and caching.
    """
    
    def __init__(
        self,
        browser_provider: BrowserProvider = None,
        html_parser: HTMLParser = None,
        cache_provider: CacheProvider = None
    ):
        """
        Initialize scraper with dependencies.
        
        Args:
            browser_provider: Browser automation provider
            html_parser: HTML parser
            cache_provider: Cache provider
        """
        self.browser = browser_provider or PlaywrightBrowserProvider()
        self.parser = html_parser or BeautifulSoupParser()
        self.cache = cache_provider or InMemoryCache()
    
    async def scrape(
        self,
        url: str,
        extraction_rules: Dict[str, ExtractionRule],
        use_cache: bool = True
    ) -> ScrapedData:
        """
        Scrape URL with extraction rules.
        
        Args:
            url: URL to scrape
            extraction_rules: Dictionary of field_name -> ExtractionRule
            use_cache: Whether to use cache
            
        Returns:
            ScrapedData object with results
        """
        try:
            # Check cache
            if use_cache and settings.cache_enabled:
                cache_key = f"scrape:{url}"
                cached = await self.cache.get(cache_key)
                if cached:
                    return ScrapedData(
                        url=url,
                        data={"cached": True},
                        metadata={"from_cache": True},
                        success=True
                    )
            
            # Fetch page
            html = await self.browser.fetch_page(url)
            
            # Parse HTML
            soup = self.parser.parse(html)
            
            # Extract title
            title_elem = soup.select_one('title')
            title = title_elem.get_text(strip=True) if title_elem else None
            
            # Extract data using rules
            extracted_data = {}
            for field_name, rule in extraction_rules.items():
                extracted_data[field_name] = self.parser.extract(soup, rule)
            
            # Cache result
            if use_cache and settings.cache_enabled:
                await self.cache.set(cache_key, str(extracted_data), settings.cache_ttl)
            
            return ScrapedData(
                url=url,
                title=title,
                data=extracted_data,
                metadata={"timestamp": asyncio.get_event_loop().time()},
                success=True
            )
        
        except Exception as e:
            return ScrapedData(
                url=url,
                success=False,
                error=str(e)
            )
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.browser.close()


# ============================================
# Specialized Scrapers
# ============================================

class JobPostingScraper:
    """
    Specialized scraper for job postings.
    
    Demonstrates how to extend the base scraper for specific use cases.
    """
    
    def __init__(self, scraper_service: ScraperService = None):
        """
        Initialize job posting scraper.
        
        Args:
            scraper_service: Base scraper service
        """
        self.scraper = scraper_service or ScraperService()
    
    def _get_job_extraction_rules(self) -> Dict[str, ExtractionRule]:
        """Get extraction rules for job postings"""
        return {
            "title": ExtractionRule(selector="h1.job-title, h1[class*='title']"),
            "company": ExtractionRule(selector=".company-name, [class*='company']"),
            "location": ExtractionRule(selector=".location, [class*='location']"),
            "description": ExtractionRule(selector=".job-description, [class*='description']"),
            "requirements": ExtractionRule(
                selector=".requirements li, [class*='requirement']",
                multiple=True
            ),
            "salary": ExtractionRule(selector=".salary, [class*='salary']"),
        }
    
    async def scrape_job(self, url: str) -> ScrapedData:
        """
        Scrape job posting.
        
        Args:
            url: Job posting URL
            
        Returns:
            ScrapedData with job information
        """
        rules = self._get_job_extraction_rules()
        return await self.scraper.scrape(url, rules)
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.scraper.cleanup()
