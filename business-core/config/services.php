<?php

return [

    /*
    |--------------------------------------------------------------------------
    | Third Party Services
    |--------------------------------------------------------------------------
    */

    'ai' => [
        'url' => env('AI_SERVICE_URL', 'http://ai-service:8000'),
    ],

    'scraper' => [
        'url' => env('SCRAPER_SERVICE_URL', 'http://scraper-service:8000'),
    ],

];
