
import google.generativeai as genai
import os
import sys

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ API Key not found")
    sys.exit(1)

genai.configure(api_key=api_key)

print(f"🔑 Testing with API Key: {api_key[:5]}...")

try:
    print("🚀 Attempting to generate embedding...")
    result = genai.embed_content(
        model="models/embedding-001",
        content="Hello world",
        task_type="retrieval_document"
    )
    print("✅ Success! Embedding generated.")
    print(f"Values: {result['embedding'][:5]}...")
except Exception as e:
    print(f"❌ Error: {e}")
