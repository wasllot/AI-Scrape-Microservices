<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use Illuminate\Http\JsonResponse;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Redis;
use Illuminate\Support\Facades\Http;
use App\Contracts\AIServiceInterface;
use App\Services\ScraperServiceClient;
use Exception;

/**
 * System Health Controller
 * 
 * Centralized health check endpoint that verifies the status of all system components:
 * - Database (PostgreSQL)
 * - Redis
 * - AI Service
 * - Scraper Service
 */
class SystemHealthController extends Controller
{
    protected AIServiceInterface $aiService;
    protected ScraperServiceClient $scraperService;

    /**
     * Check system health
     * 
     * Performs health checks on all system components with timeouts and graceful error handling.
     * Always returns 200 OK with JSON, even if components are down.
     * 
     * @return JsonResponse
     */
    public function __construct(AIServiceInterface $aiService, ScraperServiceClient $scraperService)
    {
        $this->aiService = $aiService;
        $this->scraperService = $scraperService;
    }

    /**
     * @OA\Get(
     *     path="/api/system-status",
     *     tags={"System"},
     *     summary="Check System Health",
     *     description="Verifies status of Database, Redis, AI Service, and Scraper Service.",
     *     @OA\Response(
     *         response=200,
     *         description="System status report",
     *         @OA\JsonContent(
     *             @OA\Property(property="global_status", type="string", enum={"healthy", "degraded", "down"}, example="healthy"),
     *             @OA\Property(property="timestamp", type="string", format="date-time"),
     *             @OA\Property(property="total_check_time_ms", type="number", format="float"),
     *             @OA\Property(
     *                 property="services",
     *                 type="object",
     *                 @OA\Property(
     *                     property="database",
     *                     type="object",
     *                     @OA\Property(property="status", type="string", example="up"),
     *                     @OA\Property(property="latency_ms", type="number")
     *                 ),
     *                 @OA\Property(
     *                     property="ai_service",
     *                     type="object",
     *                     @OA\Property(property="status", type="string", example="up"),
     *                     @OA\Property(property="url", type="string")
     *                 )
     *             )
     *         )
     *     )
     * )
     */
    public function check(): JsonResponse
    {
        $services = [];
        $startTime = microtime(true);

        // Check Database
        $services['database'] = $this->checkDatabase();

        // Check Redis
        $services['redis'] = $this->checkRedis();

        // Check AI Service
        $services['ai_service'] = $this->checkMicroservice(
            'http://ai-service:8000/health',
            'ai-service'
        );

        // Check Scraper Service
        $services['scraper_service'] = $this->checkMicroservice(
            'http://scraper-service:8000/health',
            'scraper-service'
        );

        // Determine global status
        $globalStatus = $this->determineGlobalStatus($services);

        $totalTime = round((microtime(true) - $startTime) * 1000, 2);

        return response()->json([
            'global_status' => $globalStatus,
            'timestamp' => now()->toIso8601String(),
            'total_check_time_ms' => $totalTime,
            'services' => $services,
        ], 200);
    }

    /**
     * Check database connection
     * 
     * @return array
     */
    private function checkDatabase(): array
    {
        $startTime = microtime(true);

        try {
            DB::connection()->getPdo();
            $latency = round((microtime(true) - $startTime) * 1000, 2);

            return [
                'status' => 'up',
                'latency_ms' => $latency,
                'details' => 'PostgreSQL connection successful',
            ];
        } catch (Exception $e) {
            $latency = round((microtime(true) - $startTime) * 1000, 2);

            return [
                'status' => 'down',
                'latency_ms' => $latency,
                'details' => 'Database connection failed',
                'error' => $e->getMessage(),
            ];
        }
    }

    /**
     * Check Redis connection
     * 
     * @return array
     */
    private function checkRedis(): array
    {
        $startTime = microtime(true);

        try {
            Redis::ping();
            $latency = round((microtime(true) - $startTime) * 1000, 2);

            return [
                'status' => 'up',
                'latency_ms' => $latency,
                'details' => 'Redis ping successful',
            ];
        } catch (Exception $e) {
            $latency = round((microtime(true) - $startTime) * 1000, 2);

            return [
                'status' => 'down',
                'latency_ms' => $latency,
                'details' => 'Redis connection failed',
                'error' => $e->getMessage(),
            ];
        }
    }

    /**
     * Check microservice health
     * 
     * @param string $url Health check URL
     * @param string $serviceName Service name for logging
     * @return array
     */
    private function checkMicroservice(string $url, string $serviceName): array
    {
        $startTime = microtime(true);

        try {
            $response = Http::timeout(2)->get($url);
            $latency = round((microtime(true) - $startTime) * 1000, 2);

            if ($response->successful()) {
                $body = $response->json();

                return [
                    'status' => 'up',
                    'latency_ms' => $latency,
                    'url' => $url,
                    'details' => 'Service responded successfully',
                    'service_status' => $body['status'] ?? 'unknown',
                ];
            } else {
                return [
                    'status' => 'down',
                    'latency_ms' => $latency,
                    'url' => $url,
                    'details' => 'Service returned error status',
                    'http_code' => $response->status(),
                ];
            }
        } catch (Exception $e) {
            $latency = round((microtime(true) - $startTime) * 1000, 2);

            return [
                'status' => 'down',
                'latency_ms' => $latency,
                'url' => $url,
                'details' => 'Service unreachable or timeout',
                'error' => $e->getMessage(),
            ];
        }
    }

    /**
     * Determine global system status
     * 
     * Logic:
     * - healthy: All services are up
     * - degraded: Some services are down but core (DB/Redis) is up
     * - down: Database or Redis is down
     * 
     * @param array $services
     * @return string
     */
    private function determineGlobalStatus(array $services): string
    {
        // If database or Redis is down, system is down
        if ($services['database']['status'] === 'down' || $services['redis']['status'] === 'down') {
            return 'down';
        }

        // Check if all services are up
        $allUp = true;
        foreach ($services as $service) {
            if ($service['status'] === 'down') {
                $allUp = false;
                break;
            }
        }

        return $allUp ? 'healthy' : 'degraded';
    }
}
