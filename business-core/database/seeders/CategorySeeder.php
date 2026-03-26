<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Str;

class CategorySeeder extends Seeder
{
    public function run(): void
    {
        $categories = [
            'Electrónica',
            'Ropa y Accesorios',
            'Hogar y Muebles',
            'Deportes y Fitness',
            'Juguetes',
            'Belleza y Cuidado Personal',
            'Herramientas'
        ];

        foreach ($categories as $index => $category) {
            DB::table('categories')->insertOrIgnore([
                'name' => $category,
                'slug' => Str::slug($category),
                'description' => 'Categoría de ' . $category,
                'is_active' => true,
                'sort_order' => $index,
                'created_at' => now(),
                'updated_at' => now(),
            ]);
        }
    }
}

