<?php

namespace Tests\Unit\Services;

use Tests\TestCase;
use App\Services\AIServiceClient;
use App\Contracts\HttpClientInterface;
use Mockery;

/**
 * Unit Tests for AI Service Client
 * 
 * Tests with mocked HTTP client following AAA pattern
 */
class AIServiceClientTest extends TestCase
{
    private $mockHttpClient;
    private AIServiceClient $aiService;

    /**
     * Set up test dependencies
     */
    protected function setUp(): void
    {
        parent::setUp();

        // Arrange: Create mock HTTP client
        $this->mockHttpClient = Mockery::mock(HttpClientInterface::class);
        $this->aiService = new AIServiceClient($this->mockHttpClient, 'http://test-ai:8000');
    }

    /**
     * Clean up after tests
     */
    protected function tearDown(): void
    {
        Mockery::close();
        parent::tearDown();
    }

    /**
     * Test successful content ingestion
     */
    public function test_ingest_success(): void
    {
        // Arrange
        $content = 'Test content';
        $metadata = ['type' => 'test'];
        $source = 'unit-test';

        $expectedResponse = [
            'success' => true,
            'embedding_id' => 123,
            'message' => 'Successfully ingested'
        ];

        $this->mockHttpClient
            ->shouldReceive('post')
            ->once()
            ->with(
                'http://test-ai:8000/ingest',
                [
                    'content' => $content,
                    'metadata' => $metadata,
                    'source' => $source
                ]
            )
            ->andReturn($expectedResponse);

        // Act
        $result = $this->aiService->ingest($content, $metadata, $source);

        // Assert
        $this->assertEquals($expectedResponse, $result);
        $this->assertTrue($result['success']);
        $this->assertEquals(123, $result['embedding_id']);
    }

    /**
     * Test ingestion failure handling
     */
    public function test_ingest_failure(): void
    {
        // Arrange
        $this->mockHttpClient
            ->shouldReceive('post')
            ->once()
            ->andThrow(new \Exception('Network error'));

        // Act & Assert
        $this->expectException(\Exception::class);
        $this->expectExceptionMessage('Network error');

        $this->aiService->ingest('Test content');
    }

    /**
     * Test successful chat query
     */
    public function test_chat_success(): void
    {
        // Arrange
        $question = 'What is the answer?';
        $conversationId = 'test-conv-123';

        $expectedResponse = [
            'answer' => 'The answer is 42',
            'sources' => [
                ['id' => 1, 'content' => 'Source 1']
            ],
            'conversation_id' => $conversationId
        ];

        $this->mockHttpClient
            ->shouldReceive('post')
            ->once()
            ->with(
                'http://test-ai:8000/chat',
                [
                    'question' => $question,
                    'max_context_items' => 5,
                    'conversation_id' => $conversationId
                ]
            )
            ->andReturn($expectedResponse);

        // Act
        $result = $this->aiService->chat($question, $conversationId);

        // Assert
        $this->assertEquals('The answer is 42', $result['answer']);
        $this->assertCount(1, $result['sources']);
        $this->assertEquals($conversationId, $result['conversation_id']);
    }

    /**
     * Test chat without conversation ID
     */
    public function test_chat_without_conversation_id(): void
    {
        // Arrange
        $question = 'Test question';

        $this->mockHttpClient
            ->shouldReceive('post')
            ->once()
            ->with(
                'http://test-ai:8000/chat',
                [
                    'question' => $question,
                    'max_context_items' => 5
                ]
            )
            ->andReturn(['answer' => 'Test answer', 'sources' => [], 'conversation_id' => 'new-id']);

        // Act
        $result = $this->aiService->chat($question);

        // Assert
        $this->assertArrayHasKey('answer', $result);
        $this->assertArrayHasKey('conversation_id', $result);
    }

    /**
     * Test health check when service is healthy
     */
    public function test_is_healthy_returns_true(): void
    {
        // Arrange
        $this->mockHttpClient
            ->shouldReceive('isAvailable')
            ->once()
            ->with('http://test-ai:8000/health')
            ->andReturn(true);

        // Act
        $result = $this->aiService->isHealthy();

        // Assert
        $this->assertTrue($result);
    }

    /**
     * Test health check when service is down
     */
    public function test_is_healthy_returns_false(): void
    {
        // Arrange
        $this->mockHttpClient
            ->shouldReceive('isAvailable')
            ->once()
            ->with('http://test-ai:8000/health')
            ->andReturn(false);

        // Act
        $result = $this->aiService->isHealthy();

        // Assert
        $this->assertFalse($result);
    }

    /**
     * Test getting base URL
     */
    public function test_get_base_url(): void
    {
        // Act
        $url = $this->aiService->getBaseUrl();

        // Assert
        $this->assertEquals('http://test-ai:8000', $url);
    }
}
