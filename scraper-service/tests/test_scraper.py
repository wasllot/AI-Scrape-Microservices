"""
Unit Tests for Scraper Service

Tests with mocking for browser and network calls.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict

from app.scrapers.base import (
    ExtractionRule,
    ScrapedData,
    BrowserProvider,
    HTMLParser,
    PlaywrightBrowserProvider,
    BeautifulSoupParser,
    ScraperService,
    JobPostingScraper
)


# ============================================
# Fixtures
# ============================================

@pytest.fixture
def mock_browser_provider():
    """Mock browser provider"""
    provider = Mock(spec=BrowserProvider)
    provider.fetch_page = AsyncMock(return_value="<html><title>Test</title><h1>Hello</h1></html>")
    provider.close = AsyncMock()
    return provider


@pytest.fixture
def mock_html_parser():
    """Mock HTML parser"""
    parser = Mock(spec=HTMLParser)
    parser.parse = Mock(return_value=Mock())
    parser.extract = Mock(return_value="Extracted data")
    return parser


@pytest.fixture
def mock_cache():
    """Mock cache provider"""
    cache = Mock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    return cache


@pytest.fixture
def scraper_service(mock_browser_provider, mock_html_parser, mock_cache):
    """Scraper service with mocked dependencies"""
    return ScraperService(
        browser_provider=mock_browser_provider,
        html_parser=mock_html_parser,
        cache_provider=mock_cache
    )


# ============================================
# Data Model Tests
# ============================================

class TestExtractionRule:
    """Tests for ExtractionRule dataclass"""
    
    def test_creation_with_defaults(self):
        """Test creating rule with default values"""
        rule = ExtractionRule(selector="h1")
        assert rule.selector == "h1"
        assert rule.attribute is None
        assert rule.multiple is False
    
    def test_creation_with_custom_values(self):
        """Test creating rule with custom values"""
        rule = ExtractionRule(
            selector="a.link",
            attribute="href",
            multiple=True
        )
        assert rule.selector == "a.link"
        assert rule.attribute == "href"
        assert rule.multiple is True


class TestScrapedData:
    """Tests for ScrapedData dataclass"""
    
    def test_successful_scrape(self):
        """Test successful scrape data"""
        data = ScrapedData(
            url="https://example.com",
            title="Example",
            data={"field": "value"},
            success=True
        )
        assert data.success is True
        assert data.error is None
    
    def test_failed_scrape(self):
        """Test failed scrape data"""
        data = ScrapedData(
            url="https://example.com",
            success=False,
            error="Connection timeout"
        )
        assert data.success is False
        assert data.error == "Connection timeout"


# ============================================
# Parser Tests
# ============================================

class TestBeautifulSoupParser:
    """Tests for BeautifulSoup parser"""
    
    def test_parse_html(self):
        """Test HTML parsing"""
        parser = BeautifulSoupParser()
        html = "<html><h1>Test</h1></html>"
        
        soup = parser.parse(html)
        
        assert soup is not None
        assert soup.h1.text == "Test"
    
    def test_extract_single_text(self):
        """Test extracting single text element"""
        parser = BeautifulSoupParser()
        html = "<html><h1 class='title'>Test Title</h1></html>"
        soup = parser.parse(html)
        
        rule = ExtractionRule(selector="h1.title")
        result = parser.extract(soup, rule)
        
        assert result == "Test Title"
    
    def test_extract_single_attribute(self):
        """Test extracting single attribute"""
        parser = BeautifulSoupParser()
        html = '<html><a href="https://example.com">Link</a></html>'
        soup = parser.parse(html)
        
        rule = ExtractionRule(selector="a", attribute="href")
        result = parser.extract(soup, rule)
        
        assert result == "https://example.com"
    
    def test_extract_multiple_elements(self):
        """Test extracting multiple elements"""
        parser = BeautifulSoupParser()
        html = "<html><li>Item 1</li><li>Item 2</li><li>Item 3</li></html>"
        soup = parser.parse(html)
        
        rule = ExtractionRule(selector="li", multiple=True)
        result = parser.extract(soup, rule)
        
        assert result == ["Item 1", "Item 2", "Item 3"]
    
    def test_extract_nonexistent_element(self):
        """Test extracting non-existent element returns None"""
        parser = BeautifulSoupParser()
        html = "<html><h1>Test</h1></html>"
        soup = parser.parse(html)
        
        rule = ExtractionRule(selector="h2")
        result = parser.extract(soup, rule)
        
        assert result is None


# ============================================
# Scraper Service Tests
# ============================================

class TestScraperService:
    """Tests for scraper service"""
    
    @pytest.mark.asyncio
    async def test_scrape_success(
        self,
        scraper_service,
        mock_browser_provider,
        mock_html_parser
    ):
        """Test successful scraping"""
        url = "https://example.com"
        rules = {"title": ExtractionRule(selector="h1")}
        
        result = await scraper_service.scrape(url, rules, use_cache=False)
        
        assert result.success is True
        assert result.url == url
        mock_browser_provider.fetch_page.assert_called_once_with(url)
    
    @pytest.mark.asyncio
    async def test_scrape_with_cache_hit(
        self,
        scraper_service,
        mock_browser_provider,
        mock_cache
    ):
        """Test scraping with cache hit"""
        url = "https://example.com"
        rules = {"title": ExtractionRule(selector="h1")}
        mock_cache.get.return_value = '{"title": "Cached"}'
        
        result = await scraper_service.scrape(url, rules, use_cache=True)
        
        assert result.success is True
        mock_cache.get.assert_called_once()
        # Browser should not be called if cache hit
        mock_browser_provider.fetch_page.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_scrape_failure(
        self,
        scraper_service,
        mock_browser_provider
    ):
        """Test scraping failure handling"""
        url = "https://example.com"
        rules = {"title": ExtractionRule(selector="h1")}
        mock_browser_provider.fetch_page.side_effect = Exception("Network error")
        
        result = await scraper_service.scrape(url, rules, use_cache=False)
        
        assert result.success is False
        assert "Network error" in result.error
    
    @pytest.mark.asyncio
    async def test_cleanup(self, scraper_service, mock_browser_provider):
        """Test cleanup calls browser close"""
        await scraper_service.cleanup()
        
        mock_browser_provider.close.assert_called_once()


# ============================================
# Job Posting Scraper Tests
# ============================================

class TestJobPostingScraper:
    """Tests for job posting scraper"""
    
    @pytest.mark.asyncio
    async def test_scrape_job(self, mock_browser_provider, mock_html_parser, mock_cache):
        """Test job scraping with specialized rules"""
        scraper_service = ScraperService(
            browser_provider=mock_browser_provider,
            html_parser=mock_html_parser,
            cache_provider=mock_cache
        )
        job_scraper = JobPostingScraper(scraper_service=scraper_service)
        
        url = "https://example.com/job/123"
        result = await job_scraper.scrape_job(url)
        
        assert result.url == url
        mock_browser_provider.fetch_page.assert_called_once()
    
    def test_extraction_rules(self):
        """Test job extraction rules are properly defined"""
        job_scraper = JobPostingScraper()
        rules = job_scraper._get_job_extraction_rules()
        
        assert "title" in rules
        assert "company" in rules
        assert "location" in rules
        assert "description" in rules
        assert "requirements" in rules
        assert rules["requirements"].multiple is True


# ============================================
# Integration Tests
# ============================================

@pytest.mark.integration
class TestScraperIntegration:
    """Integration tests with real browser (skip in CI)"""
    
    @pytest.mark.skip(reason="Requires Playwright installation")
    @pytest.mark.asyncio
    async def test_real_scraping(self):
        """Test with real browser and website"""
        scraper = ScraperService()
        rules = {"title": ExtractionRule(selector="h1")}
        
        result = await scraper.scrape("https://example.com", rules)
        
        assert result.success is True
        await scraper.cleanup()
