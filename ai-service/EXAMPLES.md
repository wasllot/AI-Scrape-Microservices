# AI Service - Código de Ejemplo RAG

Este documento muestra ejemplos completos de cómo usar el sistema RAG con Gemini API.

## 📝 Ejemplo 1: Ingesta Simple

```python
# Este código ya está implementado en app/rag/embeddings.py

from app.rag.embeddings import EmbeddingManager
import asyncio

async def main():
    manager = EmbeddingManager()
    
    # Ingestar un documento
    cv_text = """
    María González
    Ingeniera de Software Senior
    
    Experiencia:
    - 7 años desarrollando aplicaciones web
    - Experta en Python, FastAPI y PostgreSQL
    - Arquitectura de microservicios
    - Implementación de sistemas RAG
    """
    
    embedding_id = await manager.ingest(
        content=cv_text,
        metadata={
            "type": "cv",
            "candidate": "María González",
            "date": "2026-02-15"
        }
    )
    
    print(f"✓ Embedding creado con ID: {embedding_id}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 🔍 Ejemplo 2: Búsqueda Semántica

```python
from app.rag.embeddings import EmbeddingManager
import asyncio

async def main():
    manager = EmbeddingManager()
    
    # Buscar candidatos con experiencia en Python
    results = await manager.search_similar(
        query="candidatos con experiencia en Python y microservicios",
        limit=5,
        threshold=0.7
    )
    
    print(f"Encontrados {len(results)} resultados:\n")
    
    for i, doc in enumerate(results, 1):
        print(f"{i}. Similitud: {doc['similarity']:.2f}")
        print(f"   {doc['content'][:200]}...")
        print(f"   Metadata: {doc['metadata']}\n")

if __name__ == "__main__":
    asyncio.run(main())
```

## 💬 Ejemplo 3: Chat Completo con RAG

```python
from app.rag.embeddings import EmbeddingManager
from app.rag.chat import RAGChatEngine
import asyncio

async def main():
    embedding_manager = EmbeddingManager()
    chat_engine = RAGChatEngine(embedding_manager)
    
    # Primera pregunta
    response1 = await chat_engine.generate_response(
        question="¿Qué candidatos tienen experiencia en FastAPI?"
    )
    
    print("Pregunta 1:", "¿Qué candidatos tienen experiencia en FastAPI?")
    print("Respuesta:", response1['answer'])
    print(f"Fuentes: {len(response1['sources'])} documentos")
    print(f"Conversation ID: {response1['conversation_id']}\n")
    
    # Segunda pregunta (con memoria de conversación)
    response2 = await chat_engine.generate_response(
        question="¿Y cuántos años de experiencia tiene?",
        conversation_id=response1['conversation_id']
    )
    
    print("Pregunta 2:", "¿Y cuántos años de experiencia tiene?")
    print("Respuesta:", response2['answer'])

if __name__ == "__main__":
    asyncio.run(main())
```

## 🗄️ Ejemplo 4: Consultas SQL Directas con pgvector

```python
import psycopg2
from app.database import get_db_connection

# Conectar a la base de datos
conn = get_db_connection()
cursor = conn.cursor()

# Ver todos los embeddings
cursor.execute("SELECT id, metadata, created_at FROM embeddings ORDER BY created_at DESC LIMIT 10;")
embeddings = cursor.fetchall()

for emb in embeddings:
    print(f"ID: {emb['id']}, Metadata: {emb['metadata']}, Created: {emb['created_at']}")

# Búsqueda manual por similitud (ejemplo avanzado)
# Primero necesitas el embedding de tu query
query_embedding = "[0.1, 0.2, ..., 0.768]"  # Vector de 768 dimensiones

cursor.execute(
    """
    SELECT 
        id,
        content,
        1 - (embedding <=> %s::vector) as similarity
    FROM embeddings
    WHERE 1 - (embedding <=> %s::vector) > 0.7
    ORDER BY embedding <=> %s::vector
    LIMIT 5;
    """,
    (query_embedding, query_embedding, query_embedding)
)

results = cursor.fetchall()
for r in results:
    print(f"Similarity: {r['similarity']:.2f} - {r['content'][:100]}")

conn.close()
```

## 🚀 Cómo Ejecutar estos Ejemplos

### Opción 1: Dentro del Container

```bash
# Entrar al container
docker-compose exec ai-service bash

# Crear un archivo de prueba
cat > test_rag.py << 'EOF'
# Copiar el código de ejemplo aquí
EOF

# Ejecutar
python test_rag.py
```

### Opción 2: Localmente (si tienes Python)

```bash
cd ai-service

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
export GEMINI_API_KEY="tu_api_key"
export POSTGRES_HOST="localhost"
export POSTGRES_USER="postgres"
export POSTGRES_PASSWORD="tu_password"
export POSTGRES_DB="vector_db"

# Ejecutar
python -c "
from app.rag.embeddings import EmbeddingManager
import asyncio

async def test():
    manager = EmbeddingManager()
    id = await manager.ingest('Test document', {})
    print(f'Created embedding {id}')

asyncio.run(test())
"
```

## 📊 Estructura de la Tabla de Embeddings

```sql
CREATE TABLE embeddings (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(768),        -- Vector de 768 dimensiones (Gemini embedding-001)
    metadata JSONB,               -- Información adicional en formato JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índice para búsqueda rápida (IVFFlat)
CREATE INDEX embeddings_embedding_idx ON embeddings 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

## 🔧 Operadores de pgvector

- `<=>` : Distancia coseno (0 = idéntico, 2 = opuesto)
- `<->` : Distancia euclidiana
- `<#>` : Producto interno negativo

**Ejemplo de conversión:**
```python
# Similitud = 1 - distancia_coseno
similarity = 1 - (embedding1 <=> embedding2)

# Similitud alta (cercano a 1) = documentos similares
# Similitud baja (cercano a 0) = documentos diferentes
```

## 💡 Tips de Rendimiento

1. **Batch Ingestion**: Si tienes muchos documentos, usa transacciones:

```python
conn = get_db_connection()
cursor = conn.cursor()

for doc in documents:
    embedding = await manager.generate_embedding(doc['content'])
    cursor.execute("INSERT INTO embeddings (content, embedding, metadata) VALUES (%s, %s::vector, %s)", 
                   (doc['content'], str(embedding), doc['metadata']))

conn.commit()
```

2. **Cache de Embeddings**: Gemini API tiene rate limits, considera cachear embeddings frecuentes.

3. **Ajustar el threshold**: Prueba diferentes valores (0.5 - 0.9) según tu caso de uso.

## 📚 Recursos

- [Gemini API Docs](https://ai.google.dev/docs)
- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [LangChain Docs](https://python.langchain.com/)
