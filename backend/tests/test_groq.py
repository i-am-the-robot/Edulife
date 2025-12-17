
import os
import asyncio
from groq import AsyncGroq
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")
MODEL = os.getenv("GROQ_MODEL")

print(f"Testing Groq Connection...")
print(f"API Key: {API_KEY[:5]}...{API_KEY[-4:] if API_KEY else 'None'}")
print(f"Model: {MODEL}")

async def test_connection():
    try:
        client = AsyncGroq(api_key=API_KEY)
        response = await client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        print("Success! Response:", response.choices[0].message.content)
    except Exception as e:
        print("\nERROR DETECTED:")
        print(f"{type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_connection())
