import asyncio
import aiohttp


async def main():

    url = "https://api.github.com/repos/huggingface/transformers"

    async with aiohttp.ClientSession() as session:

        async with session.get(url) as response:

            print("Status:", response.status)

            data = await response.json()

            print("Repository:", data.get("full_name"))
            print("Stars:", data.get("stargazers_count"))


asyncio.run(main())