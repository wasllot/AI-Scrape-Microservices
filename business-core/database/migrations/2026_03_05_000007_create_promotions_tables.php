<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('promotions', function (Blueprint $table) {
            $table->id();
            $table->string('name');
            $table->string('slug')->unique();
            $table->text('description')->nullable();
            $table->enum('type', ['percentage', 'fixed', 'bogo', 'free_shipping'])->default('percentage');
            $table->decimal('value', 12, 2)->nullable(); // percentage or fixed amount
            $table->decimal('min_purchase_amount', 12, 2)->nullable();
            $table->decimal('max_discount_amount', 12, 2)->nullable();
            
            $table->dateTime('starts_at');
            $table->dateTime('expires_at');
            
            $table->integer('usage_limit')->nullable();
            $table->integer('used_count')->default(0);
            $table->integer('per_user_limit')->default(1);
            
            $table->boolean('is_active')->default(true);
            $table->boolean('is_featured')->default(false);
            
            $table->enum('target', ['all', 'category', 'product', 'seller'])->default('all');
            $table->foreignId('target_category_id')->nullable()->constrained('categories')->onDelete('set null');
            $table->foreignId('target_seller_id')->nullable()->constrained('sellers')->onDelete('set null');
            
            $table->string('code')->nullable()->unique();
            $table->text('terms_conditions')->nullable();
            
            $table->timestamps();
            
            $table->index(['is_active', 'starts_at', 'expires_at']);
        });

        Schema::create('product_promotions', function (Blueprint $table) {
            $table->id();
            $table->foreignId('product_id')->constrained()->onDelete('cascade');
            $table->foreignId('promotion_id')->constrained()->onDelete('cascade');
            $table->timestamps();
            
            $table->unique(['product_id', 'promotion_id']);
        });

        Schema::create('promotion_usage', function (Blueprint $table) {
            $table->id();
            $table->foreignId('promotion_id')->constrained()->onDelete('cascade');
            $table->foreignId('user_id')->constrained()->onDelete('cascade');
            $table->foreignId('order_id')->constrained()->onDelete('cascade');
            $table->decimal('discount_amount', 12, 2);
            $table->timestamps();
            
            $table->unique(['promotion_id', 'user_id', 'order_id']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('promotion_usage');
        Schema::dropIfExists('product_promotions');
        Schema::dropIfExists('promotions');
    }
};
