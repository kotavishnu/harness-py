import json
import re
from dataclasses import dataclass, field
from typing import Callable, Any
from .browser import BrowserSession


@dataclass
class Tool:
    definition: dict
    execute: Callable[[dict], Any]


@dataclass
class ToolRegistry:
    definitions: list[dict]
    by_name: dict[str, Tool]


@dataclass
class ToolHooks:
    on_upvote_success: Callable[[str], None] | None = None
    on_stories_loaded: Callable[[list], None] | None = None


def create_tools(session: BrowserSession, hooks: ToolHooks | None = None) -> ToolRegistry:
    tools: list[Tool] = [

        Tool(
            definition={
                "type": "function",
                "function": {
                    "name": "browser_navigate",
                    "description": "Navigate the browser to a URL.",
                    "parameters": {
                        "type": "object",
                        "properties": {"url": {"type": "string"}},
                        "required": ["url"],
                    },
                },
            },
            execute=lambda args: session.navigate(args["url"]),
        ),

        Tool(
            definition={
                "type": "function",
                "function": {
                    "name": "browser_url",
                    "description": "Get the URL of the current page. Use this to detect redirects (e.g. being sent to a login page).",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
            execute=lambda args: session.get_url(),
        ),

        Tool(
            definition={
                "type": "function",
                "function": {
                    "name": "browser_get_text",
                    "description": "Get the visible text content of the current page.",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
            execute=lambda args: session.get_text(),
        ),

        Tool(
            definition={
                "type": "function",
                "function": {
                    "name": "browser_fill",
                    "description": "Fill in an input field on the current page.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "selector": {"type": "string", "description": "CSS selector for the input, e.g. \"input[name='acct']\""},
                            "value": {"type": "string", "description": "The value to type into the field."},
                        },
                        "required": ["selector", "value"],
                    },
                },
            },
            execute=lambda args: session.fill(args["selector"], args["value"]),
        ),

        Tool(
            definition={
                "type": "function",
                "function": {
                    "name": "browser_click",
                    "description": "Click an element on the current page. Also waits for any navigation that results from the click.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "selector": {"type": "string", "description": "CSS selector, e.g. \"input[type='submit']\""},
                        },
                        "required": ["selector"],
                    },
                },
            },
            execute=_make_click_execute(session, hooks),
        ),

        Tool(
            definition={
                "type": "function",
                "function": {
                    "name": "browser_get_stories",
                    "description": "Get a structured list of Hacker News stories on the current page — rank, story ID, title, and whether you've already voted. Use this instead of browser_get_text to accurately identify which story to upvote.",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
            execute=_make_get_stories_execute(session, hooks),
        ),

        Tool(
            definition={
                "type": "function",
                "function": {
                    "name": "browser_has_class",
                    "description": "Check whether the first element matching a selector has a specific CSS class. Use this to verify upvote state: check if a[id='up_12345'] has class 'nosee' before and after clicking.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "selector": {"type": "string", "description": "CSS selector for the element to check."},
                            "className": {"type": "string", "description": "The CSS class name to look for."},
                        },
                        "required": ["selector", "className"],
                    },
                },
            },
            execute=lambda args: session.has_class(args["selector"], args["className"]),
        ),

    ]

    return ToolRegistry(
        definitions=[t.definition for t in tools],
        by_name={t.definition["function"]["name"]: t for t in tools},
    )


def _make_click_execute(session: BrowserSession, hooks: ToolHooks | None):
    async def execute(args: dict) -> str:
        result = await session.click(args["selector"])
        if (
            hooks and hooks.on_upvote_success
            and re.search(r"up_", json.dumps(args["selector"]))
            and re.search(r"news\.ycombinator\.com/(news)?$", result)
        ):
            match = re.search(r"up_(\d+)", args["selector"])
            if match:
                hooks.on_upvote_success(match.group(1))
        return result
    return execute


def _make_get_stories_execute(session: BrowserSession, hooks: ToolHooks | None):
    async def execute(args: dict) -> str:
        result = await session.get_stories()
        if hooks and hooks.on_stories_loaded:
            try:
                stories = json.loads(result)
                hooks.on_stories_loaded(stories)
            except Exception:
                pass
        return result
    return execute
