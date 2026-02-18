"""
Script de ingesta de datos del perfil profesional de Reinaldo Tineo.
Ejecutar dentro del contenedor: python ingest_profile.py
"""
import httpx
import asyncio

PROFILE_DATA = [
    {
        "content": """
# Reinaldo Tineo - Senior Full Stack & AI Engineer

## Perfil Profesional
Ingeniero de Software especializado en Arquitectura de Microservicios, Inteligencia Artificial y Desarrollo Full Stack.
Experto en modernización de sistemas legados y construcción de soluciones escalables.

## Habilidades Técnicas
- **Lenguajes**: Python, PHP (Laravel), JavaScript/TypeScript.
- **Arquitectura**: Microservicios, Event-Driven, DDD, Clean Architecture, SOLID.
- **AI/ML**: RAG (Retrieval Augmented Generation), LangChain, Gemini, OpenAI, Vector Databases (pgvector).
- **Infraestructura**: Docker, Kubernetes, AWS, CI/CD, Traefik.
- **Bases de datos**: PostgreSQL, Redis, MySQL.

## Filosofía de Desarrollo

### Microservicios vs Monolitos
No creo en "todo microservicios". Prefiero un monolito modular bien estructurado al inicio.
Los microservicios se justifican cuando hay necesidad de escalado independiente de equipos o componentes.
La complejidad operacional debe estar justificada por el valor de negocio.

### Principios SOLID
Aplico SOLID rigurosamente para garantizar mantenibilidad:
- **S (Single Responsibility)**: Cada servicio o clase tiene una única razón para cambiar.
- **O (Open/Closed)**: Extensible sin modificar código existente (Chain of Responsibility, Strategy).
- **L (Liskov)**: Subtipos intercambiables (Protocols en Python, Interfaces en PHP).
- **I (Interface Segregation)**: Interfaces específicas para clientes.
- **D (Dependency Inversion)**: Depender de abstracciones, no concreciones.

## Soft Skills y Liderazgo
- **Resolución de Conflictos**: Enfoque en datos y pruebas objetivas técnicas, no opiniones.
- **Mentoring**: Capacitación continua del equipo en nuevas tecnologías (RAG, AI, Docker).
- **Comunicación**: Puente entre necesidades de negocio y soluciones técnicas.
- **Trabajo en equipo**: Experiencia liderando equipos multidisciplinarios en proyectos complejos.
""",
        "metadata": {"type": "profile", "section": "overview", "language": "es"},
        "source": "portfolio_v2"
    },
    {
        "content": """
## Proyectos Destacados

### Migración de E-commerce Legado
Lideré la migración de un sistema monolítico de comercio electrónico a una arquitectura de microservicios.

**Desafíos resueltos:**
- Desacoplar lógica de negocio compleja sin interrumpir operaciones.
- Mantener integridad de datos durante la transición (miles de productos, clientes, órdenes).
- Implementar comunicación asíncrona entre servicios.

**Solución implementada:**
- Estrategia Strangler Fig para migración gradual sin downtime.
- Bus de eventos (Redis Pub/Sub) para sincronización entre servicios.
- Sincronización bidireccional entre instancias PrestaShop (mayorista/minorista).

**Resultados:**
- Mejora del 40% en performance de respuesta.
- Despliegues independientes por servicio.
- Reducción del tiempo de onboarding de nuevos desarrolladores.

### Sistema RAG "Bulletproof" (Portfolio AI)
Diseño e implementación de un pipeline RAG de alta disponibilidad para portfolio personal.

**Arquitectura:**
- Chain of Responsibility para enrutamiento de LLMs (Gemini → Groq → Static).
- Circuit Breaker pattern con Redis para resiliencia ante fallos de proveedores.
- pgvector para búsqueda semántica de embeddings.

**Características:**
- Zero downtime: siempre retorna una respuesta útil.
- Fallback automático entre proveedores de LLM.
- Memoria de conversación persistente en PostgreSQL.

### Motor de Scraping Universal
Microservicio de extracción de datos web escalable.
- Integración con Playwright (JS rendering) y BeautifulSoup.
- Pipeline de limpieza y normalización de datos.
- Ingesta automática a base vectorial para búsqueda semántica.
- API REST con FastAPI para integración con otros servicios.
""",
        "metadata": {"type": "projects", "section": "recent_work", "language": "es"},
        "source": "portfolio_v2"
    },
    {
        "content": """
## Experiencia Profesional

### Situaciones Difíciles Resueltas

**Caso 1: Migración bajo presión**
Durante la migración del e-commerce, descubrimos a mitad del proyecto que el esquema de base de datos
legado tenía inconsistencias críticas (claves foráneas rotas, datos duplicados).
Solución: Implementé un proceso de validación y limpieza de datos en paralelo, con rollback automático
si se detectaban inconsistencias. Comunicación transparente con el cliente sobre el estado real.

**Caso 2: Conflicto de arquitectura en equipo**
Un miembro senior insistía en usar un ORM pesado que generaba N+1 queries.
Solución: Preparé benchmarks comparativos con datos reales del proyecto. Los números hablaron solos.
Adoptamos una solución híbrida: ORM para operaciones simples, queries optimizadas para reportes.

**Caso 3: Proveedor de LLM caído en producción**
El proveedor principal de LLM (Gemini) tuvo una interrupción durante una demo importante.
Solución: El Circuit Breaker detectó los fallos y redirigió automáticamente a Groq (Llama 3.3).
El sistema continuó funcionando sin intervención manual. La demo fue exitosa.

## Tecnologías por Categoría

**Backend:** Python (FastAPI, Django), PHP (Laravel), Node.js
**Frontend:** React, Next.js, TypeScript, Tailwind CSS
**DevOps:** Docker, Docker Compose, GitHub Actions, Nginx, Traefik
**AI/ML:** Google Gemini, Groq, LangChain, pgvector, embeddings semánticos
**Bases de datos:** PostgreSQL, MySQL, Redis, SQLite
**Patrones:** SOLID, DDD, Clean Architecture, Repository Pattern, Circuit Breaker, Chain of Responsibility
""",
        "metadata": {"type": "experience", "section": "professional", "language": "es"},
        "source": "portfolio_v2"
    }
]


async def ingest_profile():
    print("🚀 Iniciando ingesta de perfil de Reinaldo Tineo...")
    print(f"   Total de secciones a ingestar: {len(PROFILE_DATA)}\n")

    success_count = 0
    async with httpx.AsyncClient() as client:
        for item in PROFILE_DATA:
            section = item['metadata'].get('section', 'unknown')
            print(f"   📄 Procesando sección: {section}...")
            try:
                response = await client.post(
                    "http://localhost:8000/ingest",
                    json=item,
                    timeout=60.0
                )

                if response.status_code in (200, 201):
                    data = response.json()
                    print(f"   ✅ Ingestado exitosamente (ID: {data.get('embedding_id')})")
                    success_count += 1
                else:
                    print(f"   ❌ Error {response.status_code}: {response.text[:200]}")

            except Exception as e:
                print(f"   ❌ Error de conexión: {str(e)}")

    print(f"\n{'✅' if success_count == len(PROFILE_DATA) else '⚠️'} Proceso completado: {success_count}/{len(PROFILE_DATA)} secciones ingestadas.")
    if success_count > 0:
        print("   La base de conocimiento está lista para consultas RAG.")


if __name__ == "__main__":
    asyncio.run(ingest_profile())
