<?php

use App\Http\Controllers\Api\AuthController;
use App\Http\Controllers\Api\HealthController;
use App\Http\Controllers\Api\ScrapeController;
use App\Http\Controllers\Api\SystemHealthController;
use App\Http\Controllers\Api\ChatController;
use App\Http\Controllers\Api\ContactController;
use App\Http\Controllers\Api\V1\ProductController;
use App\Http\Controllers\Api\V1\CartController;
use App\Http\Controllers\Api\V1\OrderController;
use App\Http\Controllers\Api\V1\SellerController;
use App\Http\Controllers\Api\V1\CategoryController;
use App\Http\Controllers\Api\V1\ServiceController;
use App\Http\Controllers\Api\V1\UploadController;
use App\Http\Controllers\Api\V1\WishlistController;
use App\Http\Controllers\Api\V1\UserController;
use Illuminate\Support\Facades\Route;

/*
|--------------------------------------------------------------------------
| API Routes
|--------------------------------------------------------------------------
*/

// ── Public routes ──────────────────────────────────────────────────────────

Route::get('/health', [HealthController::class, 'index']);
Route::get('/system-status', [SystemHealthController::class, 'check']);
Route::post('/chat', [ChatController::class, 'chat']);
Route::post('/chat/welcome', [ChatController::class, 'welcome']);
Route::post('/contact', [ContactController::class, 'submit']);

// ── Authentication (public) ────────────────────────────────────────────────

Route::prefix('auth')->group(function () {
    Route::post('/login', [AuthController::class, 'login']);
    Route::post('/register', [AuthController::class, 'register']);
});

// ── Authentication (requires valid token) ──────────────────────────────────

Route::prefix('auth')->middleware('auth:api')->group(function () {
    Route::post('/logout', [AuthController::class, 'logout']);
    Route::post('/refresh', [AuthController::class, 'refresh']);
    Route::get('/me', [AuthController::class, 'me']);
});

// ── Protected routes ───────────────────────────────────────────────────────

Route::middleware('auth:api')->group(function () {
    Route::get('/contacts', [ContactController::class, 'index']);

    Route::prefix('scrape')->group(function () {
        Route::post('/learn', [ScrapeController::class, 'scrapeAndLearn']);
    });
});

// ── Marketplace API v1 ───────────────────────────────────────────────────

Route::prefix('v1')->group(function () {
    
    // Public routes
    Route::get('/products', [ProductController::class, 'index']);
    Route::get('/products/featured', [ProductController::class, 'featured']);
    Route::get('/products/{id}', [ProductController::class, 'show']);
    
    Route::get('/categories', [CategoryController::class, 'index']);
    Route::get('/categories/{id}', [CategoryController::class, 'show']);
    Route::get('/search/filters', [CategoryController::class, 'index']); // Alias para filtros
    
    Route::get('/services', [ServiceController::class, 'index']);
    
    Route::get('/sellers', [SellerController::class, 'index']);
    Route::get('/sellers/{id}', [SellerController::class, 'show']);
    Route::get('/stores', [SellerController::class, 'index']);
    Route::get('/stores/{id}', [SellerController::class, 'show']);
    
    // Protected routes
    Route::middleware('auth:api')->group(function () {
        
        Route::prefix('user')->group(function () {
            Route::get('/', [UserController::class, 'profile']);
            Route::get('/profile', [UserController::class, 'profile']);
            Route::put('/profile', [UserController::class, 'updateProfile']);
        });

        Route::prefix('upload')->group(function () {
            Route::post('/image', [UploadController::class, 'image']);
        });

        Route::prefix('wishlist')->group(function () {
            Route::get('/', [WishlistController::class, 'index']);
            Route::post('/', [WishlistController::class, 'store']);
            Route::delete('/{productId}', [WishlistController::class, 'destroy']);
        });

        Route::prefix('products')->group(function () {
            Route::post('/', [ProductController::class, 'store']);
            Route::put('/{id}', [ProductController::class, 'update']);
            Route::delete('/{id}', [ProductController::class, 'destroy']);
        });
        
        Route::prefix('cart')->group(function () {
            Route::get('/', [CartController::class, 'index']);
            Route::post('/', [CartController::class, 'addItem']); // Alias for root POST add
            Route::post('/items', [CartController::class, 'addItem']);
            Route::put('/', [CartController::class, 'updateItem']); // Alias for root PUT update
            Route::put('/items/{itemId}', [CartController::class, 'updateItem']);
            Route::put('/{itemId}', [CartController::class, 'updateItem']);
            Route::delete('/items/{itemId}', [CartController::class, 'removeItem']);
            Route::delete('/{itemId}', [CartController::class, 'removeItem']);
            Route::delete('/', [CartController::class, 'clear']);
        });
        
        Route::prefix('orders')->group(function () {
            Route::get('/', [OrderController::class, 'index']);
            Route::get('/{id}', [OrderController::class, 'show']);
            Route::post('/', [OrderController::class, 'store']);
            Route::get('/{id}/track', [OrderController::class, 'track']);
        });
        
        Route::prefix('sellers')->group(function () {
            Route::post('/apply', [SellerController::class, 'apply']);
            Route::get('/me', [SellerController::class, 'me']);
            Route::put('/me', [SellerController::class, 'update']);
        });
    });
});
