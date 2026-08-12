import asyncio

from scrapers.papers import run_paper_pipeline


async def main():

    print("=" * 60)
    print("AI INTELLIGENCE PIPELINE")
    print("=" * 60)

    print("\n[1] Research Papers")

    papers = await run_paper_pipeline()

    print(
        f"\nResearch papers collected: {len(papers)}"
    )

    print("\nPipeline finished.")


if __name__ == "__main__":

    asyncio.run(main())