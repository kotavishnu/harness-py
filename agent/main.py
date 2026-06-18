import asyncio
from .harness import run_harness, verify_successful_upvote, print_harness_result, HarnessOptions

MODEL = "gpt-4o-mini"#gpt-3.5-turbo-0125"#gpt-3.5-turbo-0613"#gpt-5.4-mini"#openai/gpt-3.5-turbo-0613"

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

    result = await run_harness(TASK, MODEL, HarnessOptions(
        verify=verify_successful_upvote,
        max_attempts=3,
    ))
    print_harness_result(result)


if __name__ == "__main__":
    asyncio.run(main())
