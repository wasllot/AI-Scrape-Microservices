
import google.generativeai as genai
import os

api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

print("🔍 Listing available models...")
try:
    models = [m.name for m in genai.list_models()]
    print(f"AVAILABLE_MODELS: {', '.join(models)}")
except Exception as e:
    print(f"❌ Error listing models: {e}")
