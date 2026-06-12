import json
from playwright.async_api import async_playwright, Browser, Page


class BrowserSession:
    def __init__(self):
        self._playwright = None
        self._browser: Browser | None = None
        self._page: Page | None = None

    async def open(self) -> None:
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=False)
        context = await self._browser.new_context()
        self._page = await context.new_page()

    async def navigate(self, url: str) -> str:
        await self._page.goto(url, wait_until="domcontentloaded", timeout=15000)
        return f"Navigated to {url}"

    async def get_url(self) -> str:
        return self._page.url

    async def get_text(self) -> str:
        text = await self._page.inner_text("body")
        return text[:4000]

    async def fill(self, selector: str, value: str) -> str:
        await self._page.fill(selector, value)
        return f'Filled "{selector}"'

    async def click(self, selector: str) -> str:
        # Capture element id before clicking — navigation may change the page
        element_id = await self._page.locator(selector).first.get_attribute("id")
        await self._page.click(selector, timeout=10000)
        await self._page.wait_for_load_state("domcontentloaded", timeout=10000)
        clicked = f'element id="{element_id}"' if element_id else f'"{selector}"'
        return f"Clicked {clicked} — now at {self._page.url}"

    async def get_stories(self) -> str:
        stories = await self._page.evaluate("""() => {
            return Array.from(document.querySelectorAll('.athing')).map((row, i) => {
                const id = row.id;
                const titleEl = row.querySelector('.titleline a');
                const title = titleEl ? titleEl.textContent.trim() : '(no title)';
                const upvoteEl = document.querySelector('#up_' + id);
                const alreadyVoted = upvoteEl ? upvoteEl.classList.contains('nosee') : true;
                return { rank: i + 1, id, title, alreadyVoted };
            });
        }""")
        return json.dumps(stories, indent=2)

    async def has_class(self, selector: str, class_name: str) -> str:
        el = self._page.locator(selector).first
        classes = await el.get_attribute("class") or ""
        has = class_name in classes.split()
        if has:
            return f'"{selector}" has class "{class_name}"'
        return f'"{selector}" does not have class "{class_name}"'

    async def close(self) -> None:
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._browser = None
        self._page = None
        self._playwright = None

    async def __aenter__(self):
        await self.open()
        return self

    async def __aexit__(self, *_):
        await self.close()
