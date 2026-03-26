<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Cache;

class MercadoLibreService
{
    protected string $clientId;
    protected string $clientSecret;
    protected string $accessToken;
    protected string $refreshToken;
    protected string $mode;
    protected float $markupPercent;

    public function __construct()
    {
        $this->clientId = config('services.mercadolibre.client_id', env('MELI_CLIENT_ID'));
        $this->clientSecret = config('services.mercadolibre.client_secret', env('MELI_CLIENT_SECRET'));
        $this->accessToken = config('services.mercadolibre.access_token', env('MELI_ACCESS_TOKEN'));
        $this->refreshToken = config('services.mercadolibre.refresh_token', env('MELI_REFRESH_TOKEN'));
        $this->mode = config('services.mercadolibre.mode', env('MELI_MODE', 'sandbox'));
        $this->markupPercent = (float) config('services.mercadolibre.markup_percent', env('MELI_MARKUP_PERCENT', 15));
    }

    protected function getBaseUrl(): string
    {
        return $this->mode === 'production' 
            ? 'https://api.mercadolibre.com'
            : 'https://api.mercadolibre.com';
    }

    public function searchProducts(string $query, int $limit = 20): array
    {
        $response = Http::get("{$this->getBaseUrl()}/sites/MLA/search", [
            'q' => $query,
            'limit' => $limit,
        ]);

        if (!$response->successful()) {
            throw new \Exception('Failed to search products from Mercado Libre');
        }

        $data = $response->json();
        
        return collect($data['results'] ?? [])->map(function ($item) {
            return $this->formatProduct($item);
        })->toArray();
    }

    public function getProduct(string $mlId): array
    {
        $response = Http::get("{$this->getBaseUrl()}/items/{$mlId}");

        if (!$response->successful()) {
            throw new \Exception('Failed to get product from Mercado Libre');
        }

        return $this->formatProduct($response->json());
    }

    public function getCategories(): array
    {
        $response = Http::get("{$this->getBaseUrl()}/sites/MLA/categories");

        if (!$response->successful()) {
            throw new \Exception('Failed to get categories from Mercado Libre');
        }

        return $response->json() ?? [];
    }

    protected function formatProduct(array $item): array
    {
        $originalPrice = (float) ($item['price'] ?? 0);
        $sellingPrice = $originalPrice * (1 + $this->markupPercent / 100);

        return [
            'id' => $item['id'],
            'name' => $item['title'] ?? '',
            'slug' => \Illuminate\Support\Str::slug($item['title'] ?? ''),
            'description' => $item['title'] ?? '',
            'price' => round($sellingPrice, 2),
            'original_price' => $originalPrice,
            'compare_price' => $item['original_price'] ?? null,
            'currency_id' => $item['currency_id'] ?? 'ARS',
            'available_quantity' => $item['available_quantity'] ?? 0,
            'sold_quantity' => $item['sold_quantity'] ?? 0,
            'condition' => $item['condition'] ?? 'new',
            'thumbnail' => $item['thumbnail'] ?? '',
            'pictures' => collect($item['pictures'] ?? [])->pluck('url')->toArray(),
            'permalink' => $item['permalink'] ?? '',
            'category_id' => $item['category_id'] ?? '',
            'source' => 'mercadolibre',
            'ml_id' => $item['id'],
            'ml_url' => $item['permalink'] ?? '',
            'ml_original_price' => $originalPrice,
            'attributes' => collect($item['attributes'] ?? [])->map(function ($attr) {
                return [
                    'name' => $attr['name'] ?? '',
                    'value' => $attr['value_name'] ?? '',
                ];
            })->toArray(),
        ];
    }

    public function refreshToken(): bool
    {
        if (!$this->refreshToken) {
            return false;
        }

        $response = Http::post("{$this->getBaseUrl()}/oauth/token", [
            'grant_type' => 'refresh_token',
            'client_id' => $this->clientId,
            'client_secret' => $this->clientSecret,
            'refresh_token' => $this->refreshToken,
        ]);

        if (!$response->successful()) {
            return false;
        }

        $data = $response->json();
        
        Cache::put('meli_access_token', $data['access_token'], now()->addHours(6));
        Cache::put('meli_refresh_token', $data['refresh_token'], now()->addDays(30));

        return true;
    }
}
