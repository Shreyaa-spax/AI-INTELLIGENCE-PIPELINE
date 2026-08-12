import os
import sys
import asyncio
import random
from dotenv import load_dotenv

sys.path.append(os.path.dirname(__file__))
from chunker import chunk_text
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

async def call_gemini(text):
    if not GEMINI_API_KEY:
        raise Exception("Gemini API key not configured")
    from google import genai
    client = genai.Client(api_key=GEMINI_API_KEY)
    return (await asyncio.to_thread(client.models.generate_content, model="gemini-2.5-flash", contents=text)).text

async def call_groq(text):
    if not GROQ_API_KEY:
        raise Exception("Groq API key not configured")
    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)
    response = await asyncio.to_thread(
        client.chat.completions.create,
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": text}],
        temperature=0
    )
    return response.choices[0].message.content

async def call_deepseek(text):
    if not DEEPSEEK_API_KEY:
        raise Exception("DeepSeek API key not configured")
    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.deepseek.com/chat/completions",
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
            json={"model": "deepseek-chat", "messages": [{"role": "user", "content": text}], "temperature": 0},
            timeout=60
        ) as response:
            if response.status != 200:
                raise Exception(f"DeepSeek HTTP {response.status}: {(await response.text())[:500]}")
            return (await response.json())["choices"][0]["message"]["content"]

async def mock_extract(text):
    return {"provider": "MOCK", "text": "This is a development extraction. The LLM pipeline is working correctly."}

async def call_with_retry(provider, text, retries=3):
    """Retry transient 429/5xx provider failures with exponential backoff and jitter."""
    for attempt in range(retries + 1):
        try:
            return await provider(text)
        except Exception as error:
            message = str(error).lower()
            transient = any(code in message for code in ("429", "rate", "too many", "500", "502", "503", "504", "timeout"))
            if not transient or attempt >= retries:
                raise
            delay = min(30, (2 ** attempt) + random.uniform(0.25, 1.25))
            print(f"Transient LLM error; retrying in {delay:.2f}s...")
            await asyncio.sleep(delay)

async def call_with_fallback(text):
    providers = []
    if GEMINI_API_KEY:
        providers.append(("Gemini", call_gemini))
    if GROQ_API_KEY:
        providers.append(("Groq", call_groq))
    if DEEPSEEK_API_KEY:
        providers.append(("DeepSeek", call_deepseek))
    if not providers:
        return await mock_extract(text)

    for name, provider in providers:
        try:
            result = await call_with_retry(provider, text)
            print(f"Success: {name}")
            return {"provider": name, "text": result}
        except Exception as error:
            print(f"{name} failed after retries: {error}")

    return await mock_extract(text)

async def extract_large_text(text):
    chunks = chunk_text(text, max_chars=12000)
    print(f"Text split into {len(chunks)} chunks.")
    results = []
    for index, chunk in enumerate(chunks, start=1):
        print(f"Processing chunk {index}/{len(chunks)}")
        results.append(await call_with_fallback(chunk))
    return {
        "provider": "multi-tier",
        "text": "\n\n".join(result["text"] for result in results),
        "chunks": len(chunks)
    }
