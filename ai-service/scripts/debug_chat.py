
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(os.getcwd())

from app.rag.chat import RAGChatService
from app.rag.embeddings import EmbeddingService

async def main():
    print("🚀 Starting Debug Chat...")
    try:
        embedding_service = EmbeddingService()
        service = RAGChatService(embedding_service=embedding_service)
        print("✅ Service initialized")
        
        print("❓ Asking question...")
        response = await service.generate_response(question="Cuéntame sobre tu experiencia")
        print(f"✅ Response received: {response}")
        
    except Exception as e:
        print(f"❌ Error occurred:")
        import traceback
        with open("debug_error.log", "w") as f:
            traceback.print_exc(file=f)
        print("Error written to debug_error.log")

if __name__ == "__main__":
    asyncio.run(main())
