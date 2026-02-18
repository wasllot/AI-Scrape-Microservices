# Data Ingestion Script

Script para ingestión de datos al Knowledge Base del sistema RAG.

## Uso

### Ingestar un archivo PDF
```bash
python scripts/ingest_data.py --source "path/to/document.pdf"
```

### Ingestar un archivo de texto
```bash
python scripts/ingest_data.py --source "path/to/document.txt"
```

### Ingestar desde una URL
```bash
python scripts/ingest_data.py --source "https://example.com/page"
```

### Ingestar todos los archivos de un directorio
```bash
python scripts/ingest_data.py --directory "path/to/documents/"
```

### Con metadata personalizada
```bash
python scripts/ingest_data.py --source "cv.pdf" --metadata '{"type": "cv", "candidate": "reinaldo"}'
```

### Personalizar tamaño de chunks
```bash
python scripts/ingest_data.py --source "document.pdf" --chunk-size 500
```

## Requisitos

- PostgreSQL con pgvector instalado y configurado
- Variables de entorno configuradas en `.env`
- API key de Gemini configurada

## Ejemplo de uso con el CV

```bash
# Convertir el CV a texto primero (usando pdftotext)
pdftotext "C:\Users\reina\OneDrive\Documentos\CVS\General\CV-REINALDO-TINEO.pdf" cv.txt

# Luego ingestar
python scripts/ingest_data.py --source cv.txt --metadata '{"type": "cv", "name": "Reinaldo Tineo"}'
```

## Notas

- El script divide el texto en chunks de ~1000 caracteres por defecto
- Cada chunk se convierte en un embedding y se almacena en PostgreSQL
- El contenido queda disponible para búsquedas via el endpoint `/chat`
