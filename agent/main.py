import asyncio
from .harness import run_harness, verify_successful_upvote, print_harness_result, HarnessOptions

MODEL = "openai/gpt-3.5-turbo-0613"

TASK = """
Upvote a story on Hacker News.

Go to https://news.ycombinator.com.
Call browser_get_stories to see ranked stories with their IDs and voted status.
Find the highest-ranked story where alreadyVoted is false.
Click its upvote arrow using the exact selector: a[id="up_STORYID"] (replace STORYID with the actual id).
""".strip()


async def main():
    print(f"Model: {MODEL}")
    print(f"Task:  upvote on Hacker News\n")

    result = await run_harness(TASK, MODEL, HarnessOptions(
        verify=verify_successful_upvote,
        max_attempts=3,
    ))
    print_harness_result(result)


if __name__ == "__main__":
    asyncio.run(main())
