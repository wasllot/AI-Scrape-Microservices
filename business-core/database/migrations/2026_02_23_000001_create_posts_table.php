<?php

declare(strict_types=1);

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration {
    public function up(): void
    {
        Schema::create('posts', function (Blueprint $table) {
            $table->id();
            $table->foreignId('user_id')->constrained()->cascadeOnDelete(); // Autor
            $table->string('title');
            $table->string('slug')->unique();
            $table->longText('content');
            $table->string('excerpt')->nullable();
            $table->string('cover_image')->nullable();
            $table->string('status')->default('draft'); // draft | published | archived
            $table->timestamp('published_at')->nullable();
            $table->json('seo_metadata')->nullable();    // { title, description, keywords }
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('posts');
    }
};
