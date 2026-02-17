
import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.database import get_db_connection

def check_data():
    print("🔍 Checking database content...")
    
    try:
        with get_db_connection() as db:
            # Count rows
            count = db.execute("SELECT COUNT(*) as count FROM embeddings")
            print(f"📊 Total embeddings: {count[0]['count']}")
            
            if count[0]['count'] > 0:
                # Sample one
                sample = db.execute("SELECT id, content, metadata FROM embeddings LIMIT 1")
                print(f"📄 Sample: {sample[0]}")
            else:
                print("❌ Table is empty!")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_data()
