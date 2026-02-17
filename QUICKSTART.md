# INICIO RÁPIDO - Sistema SaaS con RAG y Scraping

## ✅ Estado Actual

- ✅ Docker Compose configurado
- ✅ PostgreSQL + pgvector listo
- ✅ Redis configurado
- ✅ Traefik reverse proxy configurado
- ✅ AI Service (FastAPI + Gemini) implementado
- ✅ Scraper Service (Playwright) implementado
- ✅ Business Core (Laravel 11) instalado con servicios personalizados
- ✅ Script de inicio automatizado (`start.ps1`)

## 🔧 PASOS FINALES ANTES DE INICIAR

### 1. Configurar GEMINI_API_KEY

Abre el archivo `.env` y configura tu API key:

```bash
# En .env, reemplaza:
GEMINI_API_KEY=your_gemini_api_key_here

# Por tu API key real (obtén en: https://aistudio.google.com/app/apikey)
GEMINI_API_KEY=AIza...tu_key_real
```

### 2. Configurar Contraseña de Base de Datos

```bash
# En .env, reemplaza:
DB_PASSWORD=your_secure_password_here

# Por una contraseña segura:
DB_PASSWORD=MiPasswordSeguro123!
```

### 3. Generar Laravel APP_KEY

```bash
cd business-core
php artisan key:generate
```

Esto actualizará automáticamente el .env con la APP_KEY generada.

## 🚀 INICIAR EL SISTEMA

### Opción 1: Script Automatizado (Recomendado)

```powershell
.\start.ps1
```

### Opción 2: Manual

```bash
# Levantar todos los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f

# Verificar que todo esté corriendo
docker-compose ps
```

## 🧪 VERIFICAR QUE TODO FUNCIONA

### 1. Health Checks

```bash
# AI Service
curl http://localhost/ai/health

# Business Core
curl http://localhost/app/health

# Scraper Service
curl http://localhost/scraper/health
```

Todos deben responder con `"status": "healthy"`.

### 2. Prueba de Ingesta de Datos

```bash
curl -X POST http://localhost/ai/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Juan Pérez - Desarrollador Full Stack con 5 años de experiencia en Laravel y Python",
    "metadata": {"type": "cv", "candidate": "Juan Pérez"},
    "source": "test"
  }'
```

Debe responder con `"success": true` y un `embedding_id`.

### 3. Prueba de Chat RAG

```bash
curl -X POST http://localhost/ai/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Qué experiencia tiene el candidato en Laravel?"
  }'
```

Debe responder con una respuesta contextual basada en los datos ingestados.

### 4. Prueba de Flujo Completo (Scraping → AI)

```bash
curl -X POST http://localhost/app/scrape/learn \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "source": "test"
  }'
```

## 📊 SERVICIOS Y PUERTOS

| Servicio | URL | Puerto |
|----------|-----|--------|
| Traefik Dashboard | http://localhost:8080 | 8080 |
| AI Service | http://localhost/ai | - |
| Business Core | http://localhost/app | - |
| Scraper Service | http://localhost/scraper | - |
| PostgreSQL | localhost:5432 | 5432 |
| Redis | localhost:6379 | 6379 |

## 🔍 TROUBLESHOOTING

### Error: "GEMINI_API_KEY not found"

```bash
# Verifica que la API key esté en .env
grep GEMINI_API_KEY .env

# Si no está, agrégala:
echo "GEMINI_API_KEY=tu_api_key" >> .env

# Reinicia los servicios
docker-compose restart ai-service
```

### Error: "Database connection failed"

```bash
# Verifica que PostgreSQL esté corriendo
docker-compose ps postgres

# Ver logs
docker-compose logs postgres

# Reconstruir si es necesario
docker-compose down -v
docker-compose up -d postgres
```

### Error: "Playwright not initialized"

```bash
# Reconstruir el servicio de scraper
docker-compose build scraper-service
docker-compose up -d scraper-service
```

### Ver Logs en Tiempo Real

```bash
# Todos los servicios
docker-compose logs -f

# Un servicio específico
docker-compose logs -f ai-service
docker-compose logs -f business-core
docker-compose logs -f scraper-service
```

## 📚 PRÓXIMOS PASOS

1. **Revisar la documentación completa**: `README.md`
2. **Ver ejemplos de código Python**: `ai-service/EXAMPLES.md`
3. **Probar los endpoints**: Usa Postman o curl con los ejemplos del README
4. **Implementar autenticación**: Agregar Laravel Sanctum para proteger endpoints
5. **Deploy a producción**: Configurar SSL/TLS y variables de entorno seguras

## 🛑 DETENER EL SISTEMA

```bash
# Detener sin eliminar volúmenes (datos persisten)
docker-compose down

# Detener Y eliminar volúmenes (datos se pierden)
docker-compose down -v
```

## 📁 ESTRUCTURA FINAL

```
microservices/
├── docker-compose.yml      ✅ Orchestración completa
├── .env                    ✅ Variables configuradas
├── start.ps1              ✅ Script de inicio
├── QUICKSTART.md          ✅ Esta guía
├── README.md              ✅ Documentación completa
│
├── ai-service/            ✅ Motor RAG con Gemini
├── business-core/         ✅ Laravel 11 con servicios custom
├── scraper-service/       ✅ Scraper con Playwright
└── scripts/               ✅ Scripts de inicialización DB
```

---

**¿Listo?** Ejecuta `.\start.ps1` y empieza a usar tu sistema SaaS con RAG! 🚀
