<?php

namespace App\Jobs;

use App\Services\AIServiceClient;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;
use Illuminate\Support\Facades\Log;

class IngestDataToAI implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public $tries = 3;
    public $timeout = 120;

    protected string $content;
    protected array $metadata;
    protected string $source;

    /**
     * Create a new job instance.
     */
    public function __construct(string $content, array $metadata = [], string $source = 'unknown')
    {
        $this->content = $content;
        $this->metadata = $metadata;
        $this->source = $source;
    }

    /**
     * Execute the job.
     * 
     * Este job se ejecuta cuando el scraper termina de extraer datos.
     * Envía los datos al servicio de IA para que "aprenda" sobre nuevas ofertas.
     */
    public function handle(AIServiceClient $aiService): void
    {
        try {
            Log::info('Ingesting data to AI service', [
                'source' => $this->source,
                'content_length' => strlen($this->content),
            ]);

            $result = $aiService->ingest(
                content: $this->content,
                metadata: $this->metadata,
                source: $this->source
            );

            Log::info('Data ingested successfully', [
                'embedding_id' => $result['embedding_id'] ?? null,
            ]);

        } catch (\Exception $e) {
            Log::error('Failed to ingest data to AI service', [
                'error' => $e->getMessage(),
                'source' => $this->source,
            ]);

            // Re-throw to trigger retry mechanism
            throw $e;
        }
    }

    /**
     * Handle a job failure.
     */
    public function failed(\Throwable $exception): void
    {
        Log::error('IngestDataToAI job failed permanently', [
            'error' => $exception->getMessage(),
            'source' => $this->source,
        ]);
    }
}
