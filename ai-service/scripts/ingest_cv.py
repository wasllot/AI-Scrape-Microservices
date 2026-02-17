
import os
import sys
import asyncio
import json
from pathlib import Path
from typing import List, Dict
import pypdf

# Add parent directory to path to import app modules
sys.path.append(str(Path(__file__).parent.parent))

from app.rag.embeddings import EmbeddingService
from app.database import get_db_connection

async def ingest_pdf(pdf_path: str) -> List[Dict]:
    print(f"📄 Processing PDF: {pdf_path}")
    
    # 1. Extract text from PDF
    text = ""
    try:
        reader = pypdf.PdfReader(pdf_path)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    except Exception as e:
        print(f"❌ Error reading PDF: {e}")
        return []

    # 2. Split into chunks (Simple splitting by sections/paragraphs)
    chunks = []
    
    # Normalize text (remove multiple newlines)
    clean_text = "\n".join([line.strip() for line in text.splitlines() if line.strip()])
    
    # Split by common section headers (heuristic)
    sections = [
        "EXPERIENCIA", "EXPERIENCE", 
        "EDUCACIÓN", "EDUCATION", 
        "HABILIDADES", "SKILLS", 
        "PROYECTOS", "PROJECTS",
        "RESUMEN", "SUMMARY", "PROFILE", "PERFIL"
    ]
    
    current_chunk = ""
    current_section = "GENERAL"
    
    for line in clean_text.splitlines():
        is_header = any(section in line.upper() for section in sections) and len(line) < 30
        
        if is_header:
            if current_chunk:
                chunks.append({
                    "content": current_chunk,
                    "metadata": {"source": "cv_pdf", "section": current_section, "type": "cv_segment"}
                })
            current_section = line.strip()
            current_chunk = line + "\n"
        else:
            current_chunk += line + "\n"
            
            # Chunk limit (approx 500 chars)
            if len(current_chunk) > 500:
                 chunks.append({
                    "content": current_chunk,
                    "metadata": {"source": "cv_pdf", "section": current_section, "type": "cv_segment"}
                })
                 current_chunk = ""
    
    if current_chunk:
        chunks.append({
            "content": current_chunk,
            "metadata": {"source": "cv_pdf", "section": current_section, "type": "cv_segment"}
        })

    return chunks

async def ingest_markdown(md_path: str) -> List[Dict]:
    print(f"📄 Processing Markdown: {md_path}")
    
    if not os.path.exists(md_path):
        print(f"⚠️ File not found: {md_path}")
        return []

    with open(md_path, 'r', encoding='utf-8') as f:
        text = f.read()

    chunks = []
    current_section = "GENERAL"
    current_content = ""
    
    lines = text.splitlines()
    for line in lines:
        if line.startswith("#"):
            if current_content.strip():
                chunks.append({
                    "content": current_content.strip(),
                    "metadata": {"source": "profile_md", "section": current_section, "type": "profile_segment"}
                })
            current_section = line.lstrip("#").strip()
            current_content = line + "\n"
        else:
            current_content += line + "\n"
            
    if current_content.strip():
        chunks.append({
            "content": current_content.strip(),
            "metadata": {"source": "profile_md", "section": current_section, "type": "profile_segment"}
        })
        
    return chunks

async def ingest_all():
    # Paths
    data_dir = Path(__file__).parent.parent / "data"
    pdf_path = data_dir / "cv.pdf"
    md_path = data_dir / "profile_data.md"

    all_chunks = []
    
    # Process PDF
    if pdf_path.exists():
        all_chunks.extend(await ingest_pdf(str(pdf_path)))
    else:
        print(f"⚠️ PDF not found: {pdf_path}")

    # Process Markdown
    if md_path.exists():
        all_chunks.extend(await ingest_markdown(str(md_path)))
    else:
        print(f"⚠️ Markdown not found: {md_path}")

    print(f"🧩 Total chunks to ingest: {len(all_chunks)}")
    
    if not all_chunks:
        print("❌ No data to ingest")
        return

    # Check API Key
    from app.config import settings
    if not settings.gemini_api_key:
        print("❌ CRITICAL: GEMINI_API_KEY is missing in settings!")
        return

    # Embed and Save
    embedding_service = EmbeddingService()
    
    try:
        # Clear previous data
        with get_db_connection() as conn:
            conn.execute("DELETE FROM embeddings", fetch_results=False)
            conn.commit()
            print("🗑️  Deleted old data from 'embeddings' table")

        # Ingest new chunks
        print(f"🚀 Ingesting {len(all_chunks)} chunks...")
        success_count = 0
        
        for i, chunk in enumerate(all_chunks, 1):
            try:
                await embedding_service.ingest(
                    content=chunk["content"], 
                    metadata=json.dumps(chunk["metadata"])
                )
                print(f"   ✓ [{i}/{len(all_chunks)}] Ingested")
                success_count += 1
            except Exception as inner_e:
                print(f"   ❌ [{i}/{len(all_chunks)}] Failed: {inner_e}")
        
        if success_count == 0:
            print("\n❌ INGESTION FAILED: 0 chunks were stored.")
        elif success_count < len(all_chunks):
            print(f"\n⚠️  PARTIAL SUCCESS: {success_count}/{len(all_chunks)} chunks ingested.")
        else:
            print(f"\n✅ SUCCESS: All {success_count} chunks ingested!")
            
    except Exception as e:
        print(f"❌ Error ingesting data: {e}")


if __name__ == "__main__":
    asyncio.run(ingest_all())
