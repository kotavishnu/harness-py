import asyncio
from .browser import BrowserSession
from .tools import create_tools
from .context import create_context
from .loop import run_loop

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

    session = BrowserSession()
    try:
        await session.open()
        tools = create_tools(session)
        messages = create_context(TASK)
        result = await run_loop(MODEL, messages, tools)

        print(f"\nAnswer: {result.answer}")
        print(f"Stopped by: {result.stopped_by}")
        print(f"Iterations: {result.iterations}")
    finally:
        await session.close()


if __name__ == "__main__":
    asyncio.run(main())
