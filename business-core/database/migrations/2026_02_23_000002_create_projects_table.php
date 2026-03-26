<?php

declare(strict_types=1);

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration {
    public function up(): void
    {
        Schema::create('projects', function (Blueprint $table) {
            $table->id();
            $table->foreignId('user_id')->nullable()->constrained()->nullOnDelete(); // Cliente asignado
            $table->string('title');
            $table->string('slug')->unique();
            $table->text('description')->nullable();
            $table->string('cover_image')->nullable();
            $table->string('status')->default('draft');   // draft | active | completed | archived
            $table->string('tech_stack')->nullable();     // Ej: "Laravel, React, PostgreSQL"
            $table->string('repo_url')->nullable();
            $table->string('live_url')->nullable();
            $table->date('started_at')->nullable();
            $table->date('finished_at')->nullable();
            $table->json('seo_metadata')->nullable();     // { title, description, keywords }
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('projects');
    }
};
