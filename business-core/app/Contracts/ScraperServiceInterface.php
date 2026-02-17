<?php

namespace App\Contracts;

/**
 * Interface for Scraper Service operations
 * 
 * Defines contract for web scraping operations
 */
interface ScraperServiceInterface
{
    /**
     * Extract data from URL with custom rules
     * 
     * @param string $url URL to scrape
     * @param array $extractionRules Extraction rules
     * @param bool $useCache Whether to use cache
     * @return array Scraped data
     * @throws \Exception
     */
    public function extract(string $url, array $extractionRules, bool $useCache = true): array;

    /**
     * Scrape job posting
     * 
     * @param string $url Job posting URL
     * @return array Job data
     * @throws \Exception
     */
    public function scrapeJobPosting(string $url): array;

    /**
     * Check scraper service health
     * 
     * @return bool
     */
    public function isHealthy(): bool;
}
