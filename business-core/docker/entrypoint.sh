#!/bin/bash
set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Business Core – Startup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 0. Ensure vendor dependencies are installed (development volume mount safety)
echo "📦 Installing composer dependencies..."
composer install --no-interaction

# 1. Publish JWT config if not already present
if [ ! -f config/jwt.php ]; then
    echo "📦 Publishing JWT config..."
    php artisan vendor:publish --provider="PHPOpenSourceSaver\JWTAuth\Providers\LaravelServiceProvider" --force
fi

# 2. Generate JWT secret if not set
if [ -z "${JWT_SECRET}" ]; then
    echo "🔑 Generating JWT secret..."
    php artisan jwt:secret --force
fi

# 3. Run database migrations
echo "🛠  Running migrations..."
php artisan migrate --force

# 4. Seed admin user
echo "🌱 Seeding admin user..."
php artisan db:seed --class=AdminUserSeeder --force

# 5. Clear & cache config for performance
echo "⚡ Optimizing..."
php artisan config:cache
php artisan route:cache

echo "✅ Startup complete – launching supervisord"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
