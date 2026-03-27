<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('sellers', function (Blueprint $table) {
            $table->string('whatsapp')->nullable()->after('bank_name');
            $table->string('contact_email')->nullable()->after('whatsapp');
            $table->string('website')->nullable()->after('contact_email');
            $table->string('address')->nullable()->after('website');
            $table->json('categories')->nullable()->after('address'); // store category IDs seller specializes in
        });
    }

    public function down(): void
    {
        Schema::table('sellers', function (Blueprint $table) {
            $table->dropColumn(['whatsapp', 'contact_email', 'website', 'address', 'categories']);
        });
    }
};
