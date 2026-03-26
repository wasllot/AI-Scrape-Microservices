<?php

namespace Database\Seeders;

use App\Models\User;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\Hash;

class AdminUserSeeder extends Seeder
{
    /**
     * Create a default admin user for the system.
     *
     * Credentials can be overridden via .env:
     *   ADMIN_EMAIL=admin@example.com
     *   ADMIN_PASSWORD=change_me_in_production
     */
    public function run(): void
    {
        $email = env('ADMIN_EMAIL', 'admin@example.com');

        User::firstOrCreate(
            ['email' => $email],
            [
                'name' => env('ADMIN_NAME', 'Admin'),
                'password' => Hash::make(env('ADMIN_PASSWORD', 'password')),
            ]
        );

        $this->command->info("Admin user ensured: {$email}");
    }
}
