from typing import Callable, Awaitable
from .browser import BrowserSession
from .loop import ToolEvent


def create_login_handler(session: BrowserSession) -> Callable[[], Awaitable[ToolEvent | None]]:
    async def handler() -> ToolEvent | None:
        current_url = await session.get_url()
        if "login" not in current_url and "vote" not in current_url:
            return None

        print("\n[harness] Login redirect detected - handling automatically...")

        try:
            await session.fill("input[name='acct']", "vishnu_y")
            await session.fill("input[name='pw']", "vishnu_y")
            await session.click("input[type='submit']")

            print("[harness] Login completed - agent can continue\n")

            return ToolEvent(
                tool="harness_auto_login",
                args={},
                result=f"Harness automatically handled login at {current_url}. You are now authenticated and back at {await session.get_url()}.",
            )
        except Exception as err:
            print(f"[harness] Login failed: {err}\n")
            return ToolEvent(
                tool="harness_auto_login",
                args={},
                result=f"Harness failed to handle login at {current_url}: {err}",
            )

    return handler
