<?php

namespace Tests\Unit\Services;

use Tests\TestCase;
use App\Services\ScraperServiceClient;
use App\Contracts\HttpClientInterface;
use Mockery;

/**
 * Unit Tests for Scraper Service Client
 */
class ScraperServiceClientTest extends TestCase
{
    private $mockHttpClient;
    private ScraperServiceClient $scraperService;

    protected function setUp(): void
    {
        parent::setUp();

        $this->mockHttpClient = Mockery::mock(HttpClientInterface::class);
        $this->scraperService = new ScraperServiceClient($this->mockHttpClient, 'http://test-scraper:8001');
    }

    protected function tearDown(): void
    {
        Mockery::close();
        parent::tearDown();
    }

    /**
     * Test successful data extraction
     */
    public function test_extract_success(): void
    {
        // Arrange
        $url = 'https://example.com';
        $rules = [
            'title' => ['selector' => 'h1'],
            'price' => ['selector' => '.price']
        ];

        $expectedResponse = [
            'success' => true,
            'url' => $url,
            'data' => [
                'title' => 'Product Title',
                'price' => '$99.99'
            ]
        ];

        $this->mockHttpClient
            ->shouldReceive('post')
            ->once()
            ->with(
                'http://test-scraper:8001/extract',
                [
                    'url' => $url,
                    'extraction_rules' => $rules,
                    'use_cache' => true
                ]
            )
            ->andReturn($expectedResponse);

        // Act
        $result = $this->scraperService->extract($url, $rules);

        // Assert
        $this->assertTrue($result['success']);
        $this->assertEquals('Product Title', $result['data']['title']);
    }

    /**
     * Test job posting scraping
     */
    public function test_scrape_job_posting_success(): void
    {
        // Arrange
        $url = 'https://example.com/job/123';

        $expectedResponse = [
            'success' => true,
            'url' => $url,
            'data' => [
                'title' => 'Software Engineer',
                'company' => 'Tech Corp',
                'location' => 'Remote'
            ]
        ];

        $this->mockHttpClient
            ->shouldReceive('post')
            ->once()
            ->with(
                'http://test-scraper:8001/scrape/job-posting',
                ['url' => $url]
            )
            ->andReturn($expectedResponse);

        // Act
        $result = $this->scraperService->scrapeJobPosting($url);

        // Assert
        $this->assertTrue($result['success']);
        $this->assertEquals('Software Engineer', $result['data']['title']);
    }

    /**
     * Test health check
     */
    public function test_is_healthy(): void
    {
        // Arrange
        $this->mockHttpClient
            ->shouldReceive('isAvailable')
            ->once()
            ->with('http://test-scraper:8001/health')
            ->andReturn(true);

        // Act
        $result = $this->scraperService->isHealthy();

        // Assert
        $this->assertTrue($result);
    }
}
