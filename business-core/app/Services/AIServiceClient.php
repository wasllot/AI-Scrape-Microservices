<?php

namespace App\Services;

use App\Contracts\AIServiceInterface;
use App\Contracts\HttpClientInterface;
use Illuminate\Support\Facades\Log;

/**
 * AI Service Client
 * 
 * Handles communication with AI & RAG Engine service
 * Following SOLID principles with dependency injection
 */
class AIServiceClient implements AIServiceInterface
{
    /**
     * @var HttpClientInterface HTTP client for requests
     */
    private HttpClientInterface $httpClient;

    /**
     * @var string Base URL for AI service
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
        $this->baseUrl = $baseUrl ?? config('services.ai.url', 'http://ai-service:8000');
    }

    /**
     * {@inheritDoc}
     */
    public function ingest(string $content, array $metadata = [], string $source = 'unknown'): array
    {
        $url = "{$this->baseUrl}/ingest";

        $data = [
            'content' => $content,
            'metadata' => $metadata,
            'source' => $source,
        ];

        try {
            $response = $this->httpClient->post($url, $data);

            Log::info('AI ingestion successful', [
                'embedding_id' => $response['embedding_id'] ?? null,
                'source' => $source
            ]);

            return $response;
        } catch (\Exception $e) {
            Log::error('AI ingestion failed', [
                'error' => $e->getMessage(),
                'content_length' => strlen($content)
            ]);
            throw $e;
        }
    }

    /**
     * {@inheritDoc}
     */
    public function chat(string $question, ?string $conversationId = null, int $maxContextItems = 5): array
    {
        $url = "{$this->baseUrl}/chat";

        $data = [
            'question' => $question,
            'max_context_items' => $maxContextItems,
        ];

        if ($conversationId) {
            $data['conversation_id'] = $conversationId;
        }

        try {
            $response = $this->httpClient->post($url, $data);

            Log::info('AI chat successful', [
                'conversation_id' => $response['conversation_id'] ?? null,
                'sources_count' => count($response['sources'] ?? [])
            ]);

            return $response;
        } catch (\Exception $e) {
            Log::error('AI chat failed', [
                'error' => $e->getMessage(),
                'question' => $question
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
