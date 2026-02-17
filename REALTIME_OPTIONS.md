# Real-Time System Health Updates

## Opción 1: Polling (✅ Recomendado para empezar)

### Frontend (React/Next.js)

```javascript
import { useState, useEffect } from 'react';

export default function SystemHealthWidget() {
  const [health, setHealth] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const res = await fetch('https://api.reinaldotineo.online/app/api/system-status');
        const data = await res.json();
        setHealth(data);
        setLastUpdate(new Date());
      } catch (error) {
        console.error('Health check failed:', error);
      }
    };

    fetchHealth(); // Initial fetch
    const interval = setInterval(fetchHealth, 10000); // Every 10s

    return () => clearInterval(interval);
  }, []);

  if (!health) return <div>Loading...</div>;

  return (
    <div className="health-widget">
      <div className="header">
        <h3>System Status</h3>
        <span className={`badge ${health.global_status}`}>
          {health.global_status}
        </span>
      </div>

      <div className="services">
        {Object.entries(health.services).map(([key, service]) => (
          <div key={key} className={`service ${service.status}`}>
            <span className="name">{key.replace('_', ' ')}</span>
            <span className="latency">{service.latency_ms}ms</span>
            <span className={`indicator ${service.status}`} />
          </div>
        ))}
      </div>

      {health.droplet && (
        <div className="droplet">
          <h4>Server Metrics</h4>
          <div>CPU: {health.droplet.cpu_usage}%</div>
          <div>Memory: {health.droplet.memory} MB</div>
          <div>Region: {health.droplet.region}</div>
        </div>
      )}

      <div className="footer">
        Last updated: {lastUpdate?.toLocaleTimeString()}
      </div>
    </div>
  );
}
```

**Pros:**
- ✅ Simple de implementar
- ✅ No requiere configuración adicional en el backend
- ✅ Suficiente para monitoreo de salud (actualizaciones cada 10-30s)
- ✅ Compatible con todos los navegadores

**Cons:**
- ❌ No es "verdadero" tiempo real
- ❌ Genera tráfico constante

---

## Opción 2: Server-Sent Events (SSE)

El servidor envía actualizaciones automáticamente.

### Backend (Laravel)

```php
// business-core/app/Http/Controllers/Api/SystemHealthController.php

public function stream()
{
    return response()->stream(function () {
        while (true) {
            // Get current health status
            $health = $this->getHealthData();
            
            // Send SSE event
            echo "data: " . json_encode($health) . "\n\n";
            ob_flush();
            flush();
            
            // Wait 5 seconds before next update
            sleep(5);
            
            // Stop if client disconnects
            if (connection_aborted()) {
                break;
            }
        }
    }, 200, [
        'Content-Type' => 'text/event-stream',
        'Cache-Control' => 'no-cache',
        'X-Accel-Buffering' => 'no',
    ]);
}

private function getHealthData(): array
{
    // Reuse existing logic from check() method
    $services = [];
    $services['database'] = $this->checkDatabase();
    $services['redis'] = $this->checkRedis();
    $services['ai_service'] = $this->checkMicroservice('http://ai-service:8000/health', 'ai-service');
    $services['scraper_service'] = $this->checkMicroservice('http://scraper-service:8000/health', 'scraper-service');
    
    return [
        'global_status' => $this->determineGlobalStatus($services),
        'timestamp' => now()->toIso8601String(),
        'services' => $services,
        'droplet' => $this->getDropletMetrics(),
    ];
}
```

### Route

```php
// business-core/routes/api.php
Route::get('/system-status/stream', [SystemHealthController::class, 'stream']);
```

### Frontend

```javascript
import { useState, useEffect } from 'react';

export default function SystemHealthWidget() {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    const eventSource = new EventSource('https://api.reinaldotineo.online/app/api/system-status/stream');

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setHealth(data);
    };

    eventSource.onerror = (error) => {
      console.error('SSE error:', error);
      eventSource.close();
    };

    return () => eventSource.close();
  }, []);

  if (!health) return <div>Connecting...</div>;

  return (
    <div className="health-widget">
      {/* Same UI as polling example */}
    </div>
  );
}
```

**Pros:**
- ✅ Verdadero tiempo real
- ✅ Más eficiente que polling (una sola conexión)
- ✅ Nativo del navegador (no requiere librerías)

**Cons:**
- ❌ Unidireccional (solo servidor → cliente)
- ❌ Mantiene una conexión abierta por cliente

---

## Opción 3: WebSockets con Laravel Broadcasting

La opción más robusta para verdadero tiempo real bidireccional.

### Backend Setup

```bash
# Instalar Laravel Reverb (nuevo sistema WebSocket de Laravel)
composer require laravel/reverb

php artisan reverb:install
```

### Configuración

```php
// business-core/config/broadcasting.php
'reverb' => [
    'driver' => 'reverb',
    'app_id' => env('REVERB_APP_ID'),
    'app_key' => env('REVERB_APP_KEY'),
    'app_secret' => env('REVERB_APP_SECRET'),
    'host' => env('REVERB_HOST', '0.0.0.0'),
    'port' => env('REVERB_PORT', 8080),
],
```

### Event

```php
// business-core/app/Events/SystemHealthUpdated.php
namespace App\Events;

use Illuminate\Broadcasting\Channel;
use Illuminate\Broadcasting\InteractsWithSockets;
use Illuminate\Contracts\Broadcasting\ShouldBroadcast;

class SystemHealthUpdated implements ShouldBroadcast
{
    public function __construct(public array $health) {}

    public function broadcastOn(): Channel
    {
        return new Channel('system-health');
    }
}
```

### Broadcast Health Updates

```php
// Schedule health checks every 10 seconds
// business-core/app/Console/Kernel.php
protected function schedule(Schedule $schedule): void
{
    $schedule->call(function () {
        $controller = app(SystemHealthController::class);
        $health = $controller->getHealthData();
        broadcast(new SystemHealthUpdated($health));
    })->everyTenSeconds();
}
```

### Frontend

```javascript
import { useEffect, useState } from 'react';
import Echo from 'laravel-echo';
import Pusher from 'pusher-js';

// Configure Laravel Echo
window.Pusher = Pusher;
window.Echo = new Echo({
  broadcaster: 'reverb',
  key: process.env.NEXT_PUBLIC_REVERB_APP_KEY,
  wsHost: 'api.reinaldotineo.online',
  wsPort: 8080,
  forceTLS: true,
});

export default function SystemHealthWidget() {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    window.Echo.channel('system-health')
      .listen('SystemHealthUpdated', (event) => {
        setHealth(event.health);
      });

    return () => {
      window.Echo.leaveChannel('system-health');
    };
  }, []);

  // Same UI as previous examples
}
```

**Pros:**
- ✅ Verdadero tiempo real
- ✅ Bidireccional
- ✅ Escalable (con Redis backend)
- ✅ Sistema oficial de Laravel

**Cons:**
- ❌ Más complejo de configurar
- ❌ Requiere puerto adicional (8080)
- ❌ Más recursos del servidor

---

## Recomendación

| Escenario | Opción Recomendada |
|-----------|-------------------|
| Widget simple de monitoreo | **Polling (Opción 1)** |
| Dashboard en tiempo real | **SSE (Opción 2)** |
| App compleja con interacciones | **WebSockets (Opción 3)** |

Para tu caso de uso (widget de salud del sistema), **Opción 1 (Polling)** es perfecta. Es simple, confiable, y actualizaciones cada 10-30 segundos son totalmente aceptables para monitoreo de salud.

Si más adelante necesitas notificaciones instantáneas (ej: alertas cuando un servicio cae), entonces considera SSE o WebSockets.
