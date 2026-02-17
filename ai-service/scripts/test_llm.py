
import os
import sys
sys.path.append(os.getcwd())
import google.generativeai as genai
from app.config import settings

print(f"🔑 API Key from settings: {settings.gemini_api_key[:5]}...")
print(f"🤖 Model from settings: {settings.chat_model}")

try:
    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(settings.chat_model)
    print("🚀 Generating content...")
    response = model.generate_content("Hola, ¿estás funcionando?")
    print(f"✅ Response: {response.text}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
