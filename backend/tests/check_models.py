
import os
import asyncio
from groq import AsyncGroq
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")

async def list_models():
    print(f"Checking models for key: {API_KEY[:5]}...")
    try:
        client = AsyncGroq(api_key=API_KEY)
        models = await client.models.list()
        print("\nAvailable Models:")
        for m in models.data:
            print(f"- {m.id}")
            
    except Exception as e:
        print(f"\nError listing models: {e}")

if __name__ == "__main__":
    asyncio.run(list_models())
