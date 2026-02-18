"""
Data Ingestion Script for Knowledge Base Population

This script extracts text from various sources (PDF, TXT, URLs) and ingests
them into the vector database for the RAG system.

Usage:
    python scripts/ingest_data.py --source path/to/document.pdf
    python scripts/ingest_data.py --source path/to/file.txt
    python scripts/ingest_data.py --source https://example.com
    python scripts/ingest_data.py --directory path/to/documents/
"""
import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# ── MUST be done BEFORE any app/third-party imports ──────────────────────────
# The script lives at /app/scripts/ingest_data.py.
# App modules (config, database, rag, ...) live at /app/app/*.
# We need BOTH /app and /app/app on sys.path.
_script_dir = Path(__file__).resolve().parent   # /app/scripts
_root_dir   = _script_dir.parent                # /app
_app_dir    = _root_dir / "app"                 # /app/app
sys.path.insert(0, str(_app_dir))
sys.path.insert(0, str(_root_dir))
os.environ.setdefault('ENV', 'development')
# ─────────────────────────────────────────────────────────────────────────────


# Third-party imports
from pypdf import PdfReader
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai

# App imports (work now because sys.path was set above)
from config import get_settings
from database import get_db_connection
from rag.embeddings import GeminiEmbeddingProvider


class TextExtractor:
    """Extract text from various sources"""
    
    @staticmethod
    def from_pdf(file_path: str) -> str:
        """Extract text from PDF"""
        try:
            reader = PdfReader(file_path)
            text_parts = []
            
            for page_num, page in enumerate(reader.pages, 1):
                text = page.extract_text()
                if text:
                    text_parts.append(f"[Page {page_num}]\n{text}")
            
            return "\n\n".join(text_parts)
        except Exception as e:
            print(f"Error reading PDF {file_path}: {e}")
            return ""
    
    @staticmethod
    def from_txt(file_path: str) -> str:
        """Extract text from plain text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading TXT {file_path}: {e}")
            return ""
    
    @staticmethod
    def from_url(url: str) -> str:
        """Extract text from URL"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove scripts and styles
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text
            text = soup.get_text(separator='\n')
            
            # Clean up whitespace
            lines = (line.strip() for line in text.split('\n'))
            lines = [line for line in lines if line]
            return '\n'.join(lines)
        except Exception as e:
            print(f"Error fetching URL {url}: {e}")
            return ""
    
    @staticmethod
    def from_directory(dir_path: str, extensions: List[str] = None) -> List[Dict[str, str]]:
        """Extract text from all files in directory"""
        if extensions is None:
            extensions = ['.pdf', '.txt']
        
        files_data = []
        dir_path = Path(dir_path)
        
        for ext in extensions:
            for file_path in dir_path.rglob(f'*{ext}'):
                print(f"Processing: {file_path}")
                
                if ext == '.pdf':
                    text = TextExtractor.from_pdf(str(file_path))
                elif ext == '.txt':
                    text = TextExtractor.from_txt(str(file_path))
                else:
                    continue
                
                if text:
                    files_data.append({
                        'source': str(file_path.name),
                        'content': text,
                        'file_path': str(file_path)
                    })
        
        return files_data


class TextChunker:
    """Split text into chunks for embedding"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_text(self, text: str) -> List[Dict[str, Any]]:
        """Split text into overlapping chunks"""
        chunks = []
        
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # If single paragraph is too long, split by sentences
            if len(current_chunk) + len(para) > self.chunk_size:
                if current_chunk:
                    chunks.append({
                        'content': current_chunk.strip(),
                        'char_count': len(current_chunk)
                    })
                
                # Start new chunk
                if len(para) > self.chunk_size:
                    # Split long paragraph
                    sentences = para.split('. ')
                    current_chunk = ""
                    for sent in sentences:
                        if len(current_chunk) + len(sent) > self.chunk_size:
                            if current_chunk:
                                chunks.append({
                                    'content': current_chunk.strip(),
                                    'char_count': len(current_chunk)
                                })
                            current_chunk = sent
                        else:
                            current_chunk += sent + ". "
                else:
                    current_chunk = para
            else:
                current_chunk += para + "\n\n"
        
        # Don't forget last chunk
        if current_chunk.strip():
            chunks.append({
                'content': current_chunk.strip(),
                'char_count': len(current_chunk)
            })
        
        # Add metadata
        for i, chunk in enumerate(chunks):
            chunk['chunk_id'] = i
            chunk['total_chunks'] = len(chunks)
        
        return chunks


class DataIngester:
    """Ingest data into vector database"""
    
    def __init__(self):
        self.settings = get_settings()
        self.db = get_db_connection()
        self.embedding_provider = GeminiEmbeddingProvider()
    
    def ingest_chunks(
        self,
        chunks: List[Dict[str, Any]],
        source_name: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Ingest text chunks into vector database"""
        
        result = {
            'source': source_name,
            'total_chunks': len(chunks),
            'successful': 0,
            'failed': 0,
            'embeddings_ids': []
        }
        
        base_metadata = metadata or {}
        base_metadata['source_name'] = source_name
        base_metadata['ingested_at'] = datetime.utcnow().isoformat()
        
        for chunk in chunks:
            try:
                # Generate embedding
                embedding = self.embedding_provider.generate_embedding(chunk['content'])
                
                # Store in database
                embedding_id = self.db.execute(
                    """
                    INSERT INTO embeddings (content, embedding, metadata, created_at)
                    VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                    RETURNING id
                    """,
                    (
                        chunk['content'],
                        embedding,
                        json.dumps({**base_metadata, 'chunk_id': chunk.get('chunk_id')})
                    ),
                    fetch_results=True
                )
                
                if embedding_id:
                    result['successful'] += 1
                    result['embeddings_ids'].append(embedding_id[0]['id'])
                
            except Exception as e:
                result['failed'] += 1
                print(f"Error ingesting chunk {chunk.get('chunk_id')}: {e}")
        
        self.db.commit()
        return result


def main():
    parser = argparse.ArgumentParser(description='Ingest data into knowledge base')
    
    parser.add_argument(
        '--source',
        type=str,
        help='Source file or URL to ingest'
    )
    
    parser.add_argument(
        '--directory',
        type=str,
        help='Directory containing files to ingest'
    )
    
    parser.add_argument(
        '--chunk-size',
        type=int,
        default=1000,
        help='Size of text chunks (default: 1000)'
    )
    
    parser.add_argument(
        '--metadata',
        type=str,
        default='{}',
        help='JSON metadata for ingested content'
    )
    
    parser.add_argument(
        '--list-sources',
        action='store_true',
        help='List available sources in directory'
    )
    
    args = parser.parse_args()
    
    # Initialize components
    extractor = TextExtractor()
    chunker = TextChunker(chunk_size=args.chunk_size)
    ingester = DataIngester()
    
    metadata = json.loads(args.metadata)
    
    if args.directory:
        # Process directory
        print(f"Processing directory: {args.directory}")
        files_data = extractor.from_directory(args.directory)
        
        for file_data in files_data:
            print(f"\nIngesting: {file_data['source']}")
            
            # Chunk text
            chunks = chunker.chunk_text(file_data['content'])
            print(f"Created {len(chunks)} chunks")
            
            # Ingest
            file_metadata = {**metadata, 'file_path': file_data.get('file_path')}
            result = ingester.ingest_chunks(
                chunks,
                file_data['source'],
                file_metadata
            )
            
            print(f"Successfully ingested: {result['successful']}/{result['total_chunks']}")
    
    elif args.source:
        # Process single source
        source = args.source
        print(f"Processing: {source}")
        
        if source.startswith('http'):
            # URL
            content = extractor.from_url(source)
            source_name = source
        elif Path(source).suffix.lower() == '.pdf':
            # PDF
            content = extractor.from_pdf(source)
            source_name = Path(source).name
        else:
            # TXT
            content = extractor.from_txt(source)
            source_name = Path(source).name
        
        if not content:
            print("No content extracted")
            return
        
        # Chunk text
        chunks = chunker.chunk_text(content)
        print(f"Created {len(chunks)} chunks")
        
        # Ingest
        result = ingester.ingest_chunks(chunks, source_name, metadata)
        
        print(f"\nIngestion complete:")
        print(f"  Source: {result['source']}")
        print(f"  Total chunks: {result['total_chunks']}")
        print(f"  Successful: {result['successful']}")
        print(f"  Failed: {result['failed']}")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
