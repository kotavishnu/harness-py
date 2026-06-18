import asyncio
from .browser import BrowserSession
from .tools import create_tools
from .context import create_context
from .loop import run_loop

MODEL = "gpt-3.5-turbo-0125"#gpt-3.5-turbo-0613"#gpt-5.4-mini"#openai/gpt-3.5-turbo-0613"

TASK = """
Upvote a story on Hacker News.


1. Go to https://news.ycombinator.com.
2. Call browser_get_stories to get ranked stories with their IDs and voted status.
3. Find the highest-ranked story where alreadyVoted is false. Note its ID.
4. Click its upvote arrow using the exact selector: a[id="up_STORYID"] (replace STORYID with the actual id).
5. If clicking redirects to a login page, call harness_auto_login to authenticate.
6. After authentication, click the same upvote arrow again: a[id="up_STORYID"].
7. You are done when the upvote click succeeds without redirecting to login.
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
