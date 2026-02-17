<?php

namespace App\Services;

use App\Contracts\HttpClientInterface;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

/**
 * Laravel HTTP Client Implementation
 * 
 * Concrete implementation of HttpClientInterface using Laravel's HTTP facade
 * Following Dependency Inversion Principle
 */
class LaravelHttpClient implements HttpClientInterface
{
    /**
     * @var int Request timeout in seconds
     */
    private int $timeout;

    /**
     * @var int Number of retry attempts
     */
    private int $retries;

    /**
     * Constructor with dependency injection
     * 
     * @param int $timeout Request timeout
     * @param int $retries Number of retries
     */
    public function __construct(int $timeout = 30, int $retries = 3)
    {
        $this->timeout = $timeout;
        $this->retries = $retries;
    }

    /**
     * {@inheritDoc}
     */
    public function get(string $url, array $headers = []): array
    {
        try {
            $response = Http::timeout($this->timeout)
                ->retry($this->retries, 100)
                ->withHeaders($headers)
                ->get($url);

            if ($response->failed()) {
                throw new \Exception("HTTP GET failed: {$response->status()}");
            }

            return $response->json();
        } catch (\Exception $e) {
            Log::error("HTTP GET error: {$e->getMessage()}", ['url' => $url]);
            throw $e;
        }
    }

    /**
     * {@inheritDoc}
     */
    public function post(string $url, array $data, array $headers = []): array
    {
        try {
            $response = Http::timeout($this->timeout)
                ->retry($this->retries, 100)
                ->withHeaders($headers)
                ->post($url, $data);

            if ($response->failed()) {
                throw new \Exception("HTTP POST failed: {$response->status()}");
            }

            return $response->json();
        } catch (\Exception $e) {
            Log::error("HTTP POST error: {$e->getMessage()}", ['url' => $url]);
            throw $e;
        }
    }

    /**
     * {@inheritDoc}
     */
    public function isAvailable(string $url): bool
    {
        try {
            $response = Http::timeout(5)->get($url);
            return $response->successful();
        } catch (\Exception $e) {
            return false;
        }
    }
}
