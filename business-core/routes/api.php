<?php

use App\Http\Controllers\Api\HealthController;
use App\Http\Controllers\Api\ScrapeController;
use App\Http\Controllers\Api\SystemHealthController;
use App\Http\Controllers\Api\ChatController;
use Illuminate\Support\Facades\Route;

/*
|--------------------------------------------------------------------------
| API Routes
|--------------------------------------------------------------------------
*/


Route::get('/health', [HealthController::class, 'index']);
Route::get('/system-status', [SystemHealthController::class, 'check']);
Route::post('/chat', [ChatController::class, 'chat']);
Route::post('/chat/welcome', [ChatController::class, 'welcome']);

Route::prefix('scrape')->group(function () {
    Route::post('/learn', [ScrapeController::class, 'scrapeAndLearn']);
});
