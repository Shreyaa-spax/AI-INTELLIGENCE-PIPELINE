import os
import asyncio
from dotenv import load_dotenv

from chunker import chunk_text

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")


async def call_gemini(text):

    print("Trying Gemini...")

    if not GEMINI_API_KEY:
        raise Exception("Gemini API key not configured")

    from google import genai

    client = genai.Client(
        api_key=GEMINI_API_KEY
    )

    response = await asyncio.to_thread(
        client.models.generate_content,
        model="gemini-2.5-flash",
        contents=text
    )

    return response.text


async def call_groq(text):

    print("Trying Groq...")

    if not GROQ_API_KEY:
        raise Exception("Groq API key not configured")

    from groq import Groq

    client = Groq(
        api_key=GROQ_API_KEY
    )

    response = await asyncio.to_thread(
        client.chat.completions.create,
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": text
            }
        ],
        temperature=0
    )

    return response.choices[0].message.content


async def call_deepseek(text):

    print("Trying DeepSeek...")

    if not DEEPSEEK_API_KEY:
        raise Exception(
            "DeepSeek API key not configured"
        )

    import aiohttp

    url = "https://api.deepseek.com/chat/completions"

    headers = {
        "Authorization":
            f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type":
            "application/json"
    }

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "user",
                "content": text
            }
        ],
        "temperature": 0
    }

    async with aiohttp.ClientSession() as session:

        async with session.post(
            url,
            headers=headers,
            json=payload,
            timeout=60
        ) as response:

            if response.status != 200:

                error = await response.text()

                raise Exception(
                    f"DeepSeek error "
                    f"{response.status}: {error}"
                )

            data = await response.json()

            return data["choices"][0]["message"]["content"]
        
async def mock_extract(text):

    print("Using MOCK LLM")

    return {
        "provider": "MOCK",
        "text": (
            "This is a development extraction. "
            "The LLM pipeline is working correctly."
        )
    }

async def call_with_fallback(text):

    providers = []

    # Only add providers when an API key exists
    if GEMINI_API_KEY:
        providers.append(
            ("Gemini", call_gemini)
        )

    if GROQ_API_KEY:
        providers.append(
            ("Groq", call_groq)
        )

    if DEEPSEEK_API_KEY:
        providers.append(
            ("DeepSeek", call_deepseek)
        )

    # No API keys available
    if not providers:

        print(
            "No LLM API keys configured."
        )

        print(
            "Using MOCK extraction."
        )

        return await mock_extract(text)

    # Try configured providers
    for name, provider in providers:

        try:

            result = await provider(text)

            print(
                f"Success: {name}"
            )

            return {
                "provider": name,
                "text": result
            }

        except Exception as error:

            print(
                f"{name} failed: {error}"
            )

    # All configured providers failed
    print(
        "All configured LLM providers failed."
    )

    print(
        "Using MOCK extraction."
    )

    return await mock_extract(text)

async def extract_large_text(text):

    chunks = chunk_text(
        text,
        max_chars=12000
    )

    print(
        f"Text split into "
        f"{len(chunks)} chunks."
    )

    results = []

    for index, chunk in enumerate(
        chunks,
        start=1
    ):

        print(
            f"\nProcessing chunk "
            f"{index}/{len(chunks)}"
        )

        result = await call_with_fallback(
            chunk
        )

        results.append(result)

    combined_text = "\n\n".join(
        result["text"]
        for result in results
    )

    return {
        "provider": "multi-tier",
        "text": combined_text,
        "chunks": len(chunks)
    }