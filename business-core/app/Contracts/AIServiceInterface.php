<?php

namespace App\Contracts;

/**
 * Interface for AI Service operations
 * 
 * Defines contract for AI/RAG operations
 * Following Interface Segregation Principle
 */
interface AIServiceInterface
{
    /**
     * Ingest content into AI service
     * 
     * @param string $content Content to ingest
     * @param array $metadata Additional metadata
     * @param string $source Source identifier
     * @return array Response with embedding_id
     * @throws \Exception
     */
    public function ingest(string $content, array $metadata = [], string $source = 'unknown'): array;

    /**
     * Query AI service with RAG
     * 
     * @param string $question User question
     * @param string|null $conversationId Optional conversation ID
     * @param int $maxContextItems Number of context items to retrieve
     * @return array Response with answer and sources
     * @throws \Exception If chat fails
     */
    public function chat(string $question, ?string $conversationId = null, int $maxContextItems = 5): array;

    /**
     * Get a smart welcome message.
     * 
     * @param string|null $conversationId Optional conversation ID
     * @return array Response with message and conversation_id
     */
    public function getWelcomeMessage(?string $conversationId = null): array;

    /**
     * Check if AI service is healthy.
     * 
     * @return bool
     */
    public function isHealthy(): bool;
}
