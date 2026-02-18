#!/usr/bin/env python3
"""Test Gemini provider"""
import traceback
import sys

try:
    from app.rag.providers.gemini import GeminiLLMProvider
    
    print("Creating Gemini provider...")
    provider = GeminiLLMProvider()
    
    print(f"Provider created. Model: {provider.model_name}")
    print("Generating response...")
    
    response = provider.generate_response("Say only: OK")
    print(f"SUCCESS: {response}")
    
except Exception as e:
    print(f"\nERROR: {type(e).__name__}: {str(e)}")
    print("\nFull traceback:")
    traceback.print_exc()
    sys.exit(1)
