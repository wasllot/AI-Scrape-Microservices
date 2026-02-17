# System Health Widget - API Documentation

## Endpoint

```
GET https://api.reinaldotineo.online/app/api/system-status
```

## Description

Returns aggregated health status of all microservices, infrastructure components, and optional DigitalOcean Droplet metrics.

## Response Format

```json
{
  "global_status": "healthy",
  "timestamp": "2026-02-17T12:40:00Z",
  "total_check_time_ms": 123.45,
  "services": {
    "database": {
      "status": "up",
      "latency_ms": 12.5,
      "details": "PostgreSQL connection successful"
    },
    "redis": {
      "status": "up",
      "latency_ms": 5.2,
      "details": "Redis ping successful"
    },
    "ai_service": {
      "status": "up",
      "latency_ms": 45.3,
      "url": "http://ai-service:8000/health",
      "details": "Service responded successfully",
      "service_status": "ok"
    },
    "scraper_service": {
      "status": "up",
      "latency_ms": 38.1,
      "url": "http://scraper-service:8000/health",
      "details": "Service responded successfully",
      "service_status": "ok"
    }
  },
  "droplet": {
    "name": "sfo2-droplet",
    "status": "active",
    "region": "San Francisco 2",
    "vcpus": 1,
    "memory": 2048,
    "disk": 50,
    "cpu_usage": 15.2
  }
}
```

## Status Values

### Global Status
- `healthy` - All services operational
- `degraded` - Some non-critical services down
- `down` - Critical services (DB/Redis) down

### Individual Service Status
- `up` - Service responding normally
- `down` - Service unreachable or erroring

## Frontend Integration

### JavaScript / Fetch API

```javascript
async function fetchSystemHealth() {
  const response = await fetch('https://api.reinaldotineo.online/app/api/system-status');
  const data = await response.json();
  
  return {
    globalStatus: data.global_status,
    services: data.services,
    droplet: data.droplet,
    timestamp: data.timestamp
  };
}

// Poll every 30 seconds
setInterval(async () => {
  const health = await fetchSystemHealth();
  updateWidget(health);
}, 30000);
```

### React Example

```jsx
import { useState, useEffect } from 'react';

function SystemHealthWidget() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const response = await fetch('https://api.reinaldotineo.online/app/api/system-status');
        const data = await response.json();
        setHealth(data);
      } catch (error) {
        console.error('Failed to fetch health:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchHealth();
    const interval = setInterval(fetchHealth, 30000); // Update every 30s

    return () => clearInterval(interval);
  }, []);

  if (loading) return <div>Loading...</div>;

  return (
    <div className="health-widget">
      <div className="status-indicator" data-status={health.global_status}>
        {health.global_status}
      </div>
      
      <div className="services">
        {Object.entries(health.services).map(([name, service]) => (
          <div key={name} className={`service ${service.status}`}>
            <span className="name">{name}</span>
            <span className="latency">{service.latency_ms}ms</span>
            <span className={`indicator ${service.status}`} />
          </div>
        ))}
      </div>

      {health.droplet && (
        <div className="droplet-metrics">
          <div>CPU: {health.droplet.cpu_usage}%</div>
          <div>Memory: {health.droplet.memory} MB</div>
          <div>Region: {health.droplet.region}</div>
        </div>
      )}
    </div>
  );
}
```

## DigitalOcean Integration (Optional)

To enable DigitalOcean metrics, add to your production `.env`:

```bash
# Get token from: https://cloud.digitalocean.com/account/api/tokens
DIGITALOCEAN_TOKEN=dop_v1_xxxxxxxxxxxxx

# Get droplet ID from: doctl compute droplet list
DIGITALOCEAN_DROPLET_ID=123456789
```

### Getting Credentials

1. **API Token:**
   - Go to: https://cloud.digitalocean.com/account/api/tokens
   - Click "Generate New Token"
   - Name: `monitoring-api` (or any name)
   - Scopes: **Read** only (no write needed)
   - Copy the token

2. **Droplet ID:**
   ```bash
   # Using doctl CLI
   doctl compute droplet list
   
   # Using API directly
   curl -X GET "https://api.digitalocean.com/v2/droplets" \
     -H "Authorization: Bearer YOUR_TOKEN" | jq '.droplets[] | {id, name}'
   ```

If credentials are not provided, the `droplet` field will be `null` in the response, and the widget will work without DigitalOcean metrics.

## Notes

- All latencies are in milliseconds
- The endpoint always returns HTTP 200 (even if services are down)
- Response times include network latency + service processing
- DigitalOcean CPU metrics are averaged over the last 5 minutes
