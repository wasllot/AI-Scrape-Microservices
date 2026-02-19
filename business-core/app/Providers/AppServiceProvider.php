<?php

namespace App\Providers;

use Illuminate\Support\ServiceProvider;
use App\Contracts\HttpClientInterface;
use App\Contracts\AIServiceInterface;
use App\Contracts\ScraperServiceInterface;
use App\Services\LaravelHttpClient;
use App\Services\AIServiceClient;
use App\Services\ScraperServiceClient;

/**
 * Service Provider for Dependency Injection
 * 
 * Binds interfaces to concrete implementations
 * Following Dependency Inversion Principle
 */
class AppServiceProvider extends ServiceProvider
{
    /**
     * Register any application services.
     */
    public function register(): void
    {
        if ($this->app->runningInConsole()) {
            if (!$this->app->bound('view')) {
                $this->app->register(\Illuminate\View\ViewServiceProvider::class);
            }
        }
        // Bind HTTP Client Interface
        $this->app->singleton(HttpClientInterface::class, function ($app) {
            return new LaravelHttpClient(
                timeout: config('services.http.timeout', 30),
                retries: config('services.http.retries', 3)
            );
        });

        // Bind AI Service Interface
        $this->app->singleton(AIServiceInterface::class, function ($app) {
            return new AIServiceClient(
                httpClient: $app->make(HttpClientInterface::class),
                baseUrl: config('services.ai.url')
            );
        });

        // Bind Scraper Service Interface
        $this->app->singleton(ScraperServiceInterface::class, function ($app) {
            return new ScraperServiceClient(
                httpClient: $app->make(HttpClientInterface::class),
                baseUrl: config('services.scraper.url')
            );
        });
    }

    /**
     * Bootstrap any application services.
     */
    public function boot(): void
    {
        //
    }
}
