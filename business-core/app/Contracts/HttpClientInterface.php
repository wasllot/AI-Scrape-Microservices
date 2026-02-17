<?php

namespace App\Contracts;

/**
 * Interface for HTTP client implementations
 * 
 * Following Dependency Inversion Principle:
 * High-level modules depend on this abstraction, not concrete implementations
 */
interface HttpClientInterface
{
    /**
     * Send GET request
     * 
     * @param string $url
     * @param array $headers
     * @return array Response data
     * @throws \Exception
     */
    public function get(string $url, array $headers = []): array;

    /**
     * Send POST request
     * 
     * @param string $url
     * @param array $data
     * @param array $headers
     * @return array Response data
     * @throws \Exception
     */
    public function post(string $url, array $data, array $headers = []): array;

    /**
     * Check if service is available
     * 
     * @param string $url
     * @return bool
     */
    public function isAvailable(string $url): bool;
}
