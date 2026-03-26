<?php

require __DIR__.'/vendor/autoload.php';

$app = require_once __DIR__.'/bootstrap/app.php';
$kernel = $app->make(Illuminate\Contracts\Console\Kernel::class);
$kernel->bootstrap();

use OpenApi\Generator;

$docsDir = __DIR__ . '/storage/api-docs';
if (!is_dir($docsDir)) {
    mkdir($docsDir, 0755, true);
}

// Manually fetch all files in Api/V1 to bypass Symfony/Finder hangs on Docker for Windows
$dir = __DIR__ . '/app/Http/Controllers/Api/V1';
$files = [__DIR__ . '/app/Http/Controllers/Controller.php'];

foreach (scandir($dir) as $file) {
    if (str_ends_with($file, '.php')) {
        $files[] = $dir . '/' . $file;
    }
}

// Generate the Swagger Docs explicitly from the PHP array
$generator = new Generator();
try {
    $swagger = $generator->generate($files);
    
    $jsonPath = $docsDir . '/api-docs.json';
    file_put_contents($jsonPath, $swagger->toJson());
    chmod($jsonPath, 0777);
    echo "Swagger JSON Successfully Generated and Saved to $jsonPath!\n";

} catch (\Exception $e) {
    echo "ERROR: " . $e->getMessage() . "\n";
}
