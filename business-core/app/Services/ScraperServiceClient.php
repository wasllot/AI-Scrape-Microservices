<?php

namespace App\Services;

use App\Contracts\ScraperServiceInterface;
use App\Contracts\HttpClientInterface;
use Illuminate\Support\Facades\Log;

/**
 * Scraper Service Client
 * 
 * Handles communication with Universal Scraper service
 * Following SOLID principles with dependency injection
 */
class ScraperServiceClient implements ScraperServiceInterface
{
    /**
     * @var HttpClientInterface HTTP client for requests
     */
    private HttpClientInterface $httpClient;

    /**
     * @var string Base URL for scraper service
     */
    private string $baseUrl;

    /**
     * Constructor with dependency injection
     * 
     * @param HttpClientInterface $httpClient HTTP client implementation
     * @param string|null $baseUrl Optional custom base URL
     */
    public function __construct(HttpClientInterface $httpClient, ?string $baseUrl = null)
    {
        $this->httpClient = $httpClient;
        $this->baseUrl = $baseUrl ?? config('services.scraper.url', 'http://scraper-service:8001');
    }

    /**
     * {@inheritDoc}
     */
    public function extract(string $url, array $extractionRules, bool $useCache = true): array
    {
        $endpoint = "{$this->baseUrl}/extract";

        $data = [
            'url' => $url,
            'extraction_rules' => $extractionRules,
            'use_cache' => $useCache,
        ];

        try {
            $response = $this->httpClient->post($endpoint, $data);

            Log::info('Scraping successful', [
                'url' => $url,
                'success' => $response['success'] ?? false
            ]);

            return $response;
        } catch (\Exception $e) {
            Log::error('Scraping failed', [
                'error' => $e->getMessage(),
                'url' => $url
            ]);
            throw $e;
        }
    }

    /**
     * {@inheritDoc}
     */
    public function scrapeJobPosting(string $url): array
    {
        $endpoint = "{$this->baseUrl}/scrape/job-posting";

        $data = ['url' => $url];

        try {
            $response = $this->httpClient->post($endpoint, $data);

            Log::info('Job scraping successful', [
                'url' => $url,
                'title' => $response['data']['title'] ?? null
            ]);

            return $response;
        } catch (\Exception $e) {
            Log::error('Job scraping failed', [
                'error' => $e->getMessage(),
                'url' => $url
            ]);
            throw $e;
        }
    }

    /**
     * {@inheritDoc}
     */
    public function isHealthy(): bool
    {
        $url = "{$this->baseUrl}/health";
        return $this->httpClient->isAvailable($url);
    }

    /**
     * Get service base URL
     * 
     * @return string
     */
    public function getBaseUrl(): string
    {
        return $this->baseUrl;
    }
}
