<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Contracts\ScraperServiceInterface;
use App\Jobs\IngestDataToAI;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Validator;

/**
 * Scrape Controller
 * 
 * Orchestrates scraping and AI ingestion workflow
 * Using dependency injection following SOLID principles
 */
class ScrapeController extends Controller
{
    /**
     * Constructor with dependency injection
     * 
     * @param ScraperServiceInterface $scraperService
     */
    public function __construct(
        private ScraperServiceInterface $scraperService
    ) {
    }

    /**
     * Scrape URL and queue for AI learning
     * 
     * Demonstrates the complete workflow:
     * 1. Scrape data from URL
     * 2. Queue for AI ingestion
     * 3. Return immediate response
     * 
     * @param Request $request
     * @return JsonResponse
     */
    public function scrapeAndLearn(Request $request): JsonResponse
    {
        // Validate request
        $validator = Validator::make($request->all(), [
            'url' => 'required|url',
            'source' => 'sometimes|string|max:255',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'errors' => $validator->errors()
            ], 422);
        }

        try {
            // Step 1: Scrape job posting
            $scrapedData = $this->scraperService->scrapeJobPosting($request->url);

            if (!$scrapedData['success']) {
                return response()->json([
                    'success' => false,
                    'message' => 'Scraping failed',
                    'error' => $scrapedData['error'] ?? 'Unknown error'
                ], 500);
            }

            // Step 2: Format data for AI ingestion
            $content = $this->formatJobDataForAI($scrapedData['data']);
            $metadata = [
                'type' => 'job_posting',
                'url' => $request->url,
                'scraped_at' => now()->toIso8601String(),
            ];

            // Step 3: Queue for AI ingestion (async)
            IngestDataToAI::dispatch($content, $metadata, $request->input('source', 'scraper'));

            return response()->json([
                'success' => true,
                'message' => 'Job scraped and queued for AI ingestion',
                'data' => [
                    'title' => $scrapedData['data']['title'] ?? null,
                    'company' => $scrapedData['data']['company'] ?? null,
                    'queued' => true,
                ],
            ]);

        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Operation failed',
                'error' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Format job data for AI ingestion
     * 
     * Single Responsibility: Only formats data
     * 
     * @param array $jobData
     * @return string
     */
    private function formatJobDataForAI(array $jobData): string
    {
        $parts = [];

        if (!empty($jobData['title'])) {
            $parts[] = "Título: {$jobData['title']}";
        }

        if (!empty($jobData['company'])) {
            $parts[] = "Empresa: {$jobData['company']}";
        }

        if (!empty($jobData['location'])) {
            $parts[] = "Ubicación: {$jobData['location']}";
        }

        if (!empty($jobData['description'])) {
            $parts[] = "Descripción: {$jobData['description']}";
        }

        if (!empty($jobData['requirements']) && is_array($jobData['requirements'])) {
            $requirements = implode(', ', $jobData['requirements']);
            $parts[] = "Requisitos: {$requirements}";
        }

        if (!empty($jobData['salary'])) {
            $parts[] = "Salario: {$jobData['salary']}";
        }

        return implode("\n\n", $parts);
    }
}
