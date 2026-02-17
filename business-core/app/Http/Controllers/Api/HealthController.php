<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Contracts\AIServiceInterface;
use App\Contracts\ScraperServiceInterface;
use Illuminate\Http\JsonResponse;

/**
 * Health Check Controller
 * 
 * Monitors system health and service dependencies
 * Using dependency injection for services
 */
class HealthController extends Controller
{
    /**
     * Constructor with dependency injection
     * 
     * @param AIServiceInterface $aiService
     * @param ScraperServiceInterface $scraperService
     */
    public function __construct(
        private AIServiceInterface $aiService,
        private ScraperServiceInterface $scraperService
    ) {
    }

    /**
     * Check overall system health
     * 
     * @return JsonResponse
     */
    public function index(): JsonResponse
    {
        $services = [
            'ai_service' => $this->aiService->isHealthy() ? 'healthy' : 'unhealthy',
            'scraper_service' => $this->scraperService->isHealthy() ? 'healthy' : 'unhealthy',
        ];

        $allHealthy = !in_array('unhealthy', $services);

        return response()->json([
            'status' => $allHealthy ? 'healthy' : 'degraded',
            'services' => $services,
            'timestamp' => now()->toIso8601String(),
        ], $allHealthy ? 200 : 503);
    }

    /**
     * Check AI service health specifically
     * 
     * @return JsonResponse
     */
    public function aiService(): JsonResponse
    {
        $healthy = $this->aiService->isHealthy();

        return response()->json([
            'service' => 'ai',
            'status' => $healthy ? 'healthy' : 'unhealthy',
            'url' => $this->aiService->getBaseUrl(),
        ], $healthy ? 200 : 503);
    }

    /**
     * Check scraper service health specifically
     * 
     * @return JsonResponse
     */
    public function scraperService(): JsonResponse
    {
        $healthy = $this->scraperService->isHealthy();

        return response()->json([
            'service' => 'scraper',
            'status' => $healthy ? 'healthy' : 'unhealthy',
            'url' => $this->scraperService->getBaseUrl(),
        ], $healthy ? 200 : 503);
    }
}
