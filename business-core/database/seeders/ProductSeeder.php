<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Str;

class ProductSeeder extends Seeder
{
    public function run(): void
    {
        $sellers = DB::table('sellers')->pluck('id')->toArray();
        $categories = DB::table('categories')->pluck('id')->toArray();

        if (empty($sellers) || empty($categories)) {
            return;
        }

        $products = [
            ['name' => 'Smartphone Galaxy 21', 'price' => 799.99, 'stock' => 50],
            ['name' => 'Laptop Pro 15', 'price' => 1299.00, 'stock' => 20],
            ['name' => 'Auriculares Inalámbricos', 'price' => 59.99, 'stock' => 100],
            ['name' => 'Smartwatch Deportivo', 'price' => 199.50, 'stock' => 30],
            ['name' => 'Cámara Reflex Digital', 'price' => 549.99, 'stock' => 15],
            ['name' => 'Monitor 4K 27"', 'price' => 329.00, 'stock' => 40],
            ['name' => 'Teclado Mecánico RGB', 'price' => 89.99, 'stock' => 60],
            ['name' => 'Ratón Gaming Inalámbrico', 'price' => 49.99, 'stock' => 80],
            ['name' => 'Silla Ergonómica Oficina', 'price' => 249.99, 'stock' => 25],
            ['name' => 'Escritorio Elevable Ajustable', 'price' => 399.00, 'stock' => 10],
        ];

        foreach ($products as $index => $item) {
            $sellerId = $sellers[array_rand($sellers)];
            $categoryId = $categories[array_rand($categories)];
            
            DB::table('products')->insertOrIgnore([
                'seller_id' => $sellerId,
                'category_id' => $categoryId,
                'name' => $item['name'],
                'slug' => Str::slug($item['name']) . '-' . rand(100, 999), // ensure unique
                'description' => 'Descripción detallada para ' . $item['name'] . '. Este es un excelente producto para todas tus necesidades.',
                'short_description' => 'Breve descripción de ' . $item['name'],
                'sku' => 'SKU-' . strtoupper(Str::random(6)),
                'price' => $item['price'],
                'stock_quantity' => $item['stock'],
                'is_active' => true,
                'is_featured' => rand(0, 1) == 1,
                'created_at' => now(),
                'updated_at' => now(),
            ]);
        }
    }
}
