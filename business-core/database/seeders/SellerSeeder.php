<?php

namespace Database\Seeders;

use App\Models\User;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Str;

class SellerSeeder extends Seeder
{
    public function run(): void
    {
        // Get the first admin user
        $adminUserId = DB::table('users')->where('email', 'admin@example.com')->value('id');
        
        if (!$adminUserId) {
            $adminUserId = DB::table('users')->insertGetId([
                'name' => 'Admin Test',
                'email' => 'admin@example.com',
                'password' => bcrypt('password'),
                'created_at' => now(),
                'updated_at' => now(),
            ]);
        }

        $sellers = [
            [
                'user_id' => $adminUserId,
                'store_name' => 'Tienda Oficial Admin',
                'slug' => 'tienda-oficial-admin',
                'description' => 'La tienda oficial de nuestra plataforma.',
                'status' => 'approved',
                'commission_rate' => 5.00,
                'rating' => 5.00,
                'approved_at' => now(),
            ]
        ];

        // Create random users for other sellers
        for ($i = 1; $i <= 3; $i++) {
            $sellerUserId = DB::table('users')->insertGetId([
                'name' => "Vendedor de Prueba $i",
                'email' => "vendedor$i@example.com",
                'password' => bcrypt('password'),
                'created_at' => now(),
                'updated_at' => now(),
            ]);

            $storeName = "Tienda de Prueba $i";
            $sellers[] = [
                'user_id' => $sellerUserId,
                'store_name' => $storeName,
                'slug' => Str::slug($storeName),
                'description' => "Descripción para tienda $i",
                'status' => 'approved',
                'commission_rate' => 10.00,
                'rating' => 4.5,
                'approved_at' => now(),
            ];
        }

        foreach ($sellers as $seller) {
            DB::table('sellers')->insertOrIgnore(array_merge($seller, [
                'created_at' => now(),
                'updated_at' => now(),
            ]));
        }
    }
}

