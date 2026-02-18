import httpx
import asyncio
import json

async def test_chat():
    print("Testing /chat endpoint...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8000/chat",
                json={"question": "Hola, ¿puedes explicarme qué son los microservicios?"},
                timeout=30.0
            )
            print(f"Status Code: {response.status_code}")
            data = response.json()
            print(f"Answer: {data.get('answer', 'NO ANSWER FOUND')}")
            print(f"Sources count: {len(data.get('sources', []))}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_chat())
