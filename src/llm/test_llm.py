import asyncio

from orchestrator import extract_large_text


async def main():

    text = """
    Artificial intelligence is transforming
    research, software development, healthcare,
    finance, education and many other industries.

    AI systems can process large amounts of data
    and help organizations discover patterns,
    automate tasks and make predictions.

    """ * 500

    result = await extract_large_text(
        text
    )

    print("\n====================")
    print("FINAL RESULT")
    print("====================")

    print(
        "Provider:",
        result["provider"]
    )

    print(
        "Chunks:",
        result["chunks"]
    )

    print(
        "Output:",
        result["text"][:1000]
    )


if __name__ == "__main__":

    asyncio.run(main())