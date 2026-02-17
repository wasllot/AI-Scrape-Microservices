<?php

use App\Http\Controllers\Api\HealthController;

Route::get('/', function () {
    return view('welcome');
});

Route::get('/health', [HealthController::class, 'index']);
