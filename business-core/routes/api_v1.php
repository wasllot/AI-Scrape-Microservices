<?php

use App\Http\Controllers\Api\V1\ProductController;
use App\Http\Controllers\Api\V1\CartController;
use App\Http\Controllers\Api\V1\OrderController;
use App\Http\Controllers\Api\V1\SellerController;
use App\Http\Controllers\Api\V1\CategoryController;
use Illuminate\Support\Facades\Route;

Route::prefix('v1')->group(function () {
    
    Route::middleware('auth:api')->group(function () {
        
        Route::prefix('products')->group(function () {
            Route::get('/', [ProductController::class, 'index']);
            Route::get('/featured', [ProductController::class, 'featured']);
            Route::get('/{id}', [ProductController::class, 'show']);
            Route::post('/', [ProductController::class, 'store']);
            Route::put('/{id}', [ProductController::class, 'update']);
            Route::delete('/{id}', [ProductController::class, 'destroy']);
        });

        Route::prefix('cart')->group(function () {
            Route::get('/', [CartController::class, 'index']);
            Route::post('/items', [CartController::class, 'addItem']);
            Route::put('/items/{itemId}', [CartController::class, 'updateItem']);
            Route::delete('/items/{itemId}', [CartController::class, 'removeItem']);
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

        Route::prefix('addresses')->group(function () {
            Route::get('/', [\App\Http\Controllers\Api\V1\AddressController::class, 'index']);
            Route::post('/', [\App\Http\Controllers\Api\V1\AddressController::class, 'store']);
            Route::put('/{id}', [\App\Http\Controllers\Api\V1\AddressController::class, 'update']);
            Route::delete('/{id}', [\App\Http\Controllers\Api\V1\AddressController::class, 'destroy']);
        });
    });

    Route::get('/products', [ProductController::class, 'index']);
    Route::get('/products/featured', [ProductController::class, 'featured']);
    Route::get('/products/{id}', [ProductController::class, 'show']);

    Route::get('/categories', [CategoryController::class, 'index']);
    Route::get('/categories/{id}', [CategoryController::class, 'show']);

    Route::get('/sellers', [SellerController::class, 'index']);
    Route::get('/sellers/{id}', [SellerController::class, 'show']);
});
