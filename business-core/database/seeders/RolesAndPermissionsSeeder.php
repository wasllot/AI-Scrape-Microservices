<?php

declare(strict_types=1);

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use Spatie\Permission\Models\Role;
use Spatie\Permission\Models\Permission;
use App\Models\User;

class RolesAndPermissionsSeeder extends Seeder
{
    /**
     * Create the default roles and a SuperAdmin user.
     */
    public function run(): void
    {
        // Reset cached roles and permissions
        app()[\Spatie\Permission\PermissionRegistrar::class]->forgetCachedPermissions();

        // ── Roles ────────────────────────────────────────────────────────────
        $superAdmin = Role::firstOrCreate(['name' => 'SuperAdmin', 'guard_name' => 'web']);
        $client = Role::firstOrCreate(['name' => 'Client', 'guard_name' => 'web']);

        // ── Permissions ──────────────────────────────────────────────────────
        $permissions = [
            // Contacts / Leads
            'view_contacts',
            'manage_contacts',

            // Blog
            'view_posts',
            'manage_posts',

            // Projects
            'view_projects',
            'manage_projects',

            // Tasks
            'view_own_tasks',
            'manage_all_tasks',
        ];

        foreach ($permissions as $permission) {
            Permission::firstOrCreate(['name' => $permission, 'guard_name' => 'web']);
        }

        // SuperAdmin gets all permissions
        $superAdmin->givePermissionTo(Permission::all());

        // Client gets restricted permissions
        $client->givePermissionTo([
            'view_projects',
            'view_own_tasks',
        ]);

        // ── Default SuperAdmin user ──────────────────────────────────────────
        /** @var User $admin */
        $admin = User::firstOrCreate(
            ['email' => config('admin.email', 'admin@example.com')],
            [
                'name' => config('admin.name', 'Admin'),
                'password' => bcrypt(config('admin.password', 'change_me_in_production')),
            ]
        );

        $admin->assignRole($superAdmin);

        $this->command->info('✅ Roles, permissions and SuperAdmin user created.');
    }
}
