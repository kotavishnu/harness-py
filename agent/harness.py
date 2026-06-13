import json
import re
from dataclasses import dataclass
from typing import Callable, Literal

from .browser import BrowserSession
from .tools import create_tools
from .context import create_context
from .guardrails import default_guardrails
from .loop import LoopIteration, run_loop


@dataclass
class VerifyResult:
    passed: bool
    reason: str
    fatal: bool = False


@dataclass
class HarnessExecutionResult:
    answer: str
    iterations: int
    trace: list[LoopIteration]
    stopped_by: Literal["model", "guardrail", "success"]
    task: str
    model: str


@dataclass
class HarnessOptions:
    verify: Callable[[HarnessExecutionResult], VerifyResult] | None = None
    max_attempts: int = 1


@dataclass
class HarnessResult:
    answer: str
    iterations: int
    trace: list[LoopIteration]
    stopped_by: Literal["model", "guardrail", "success"]
    task: str
    model: str
    attempts: int
    verification: VerifyResult | None


async def run_harness(
    task: str,
    model: str,
    options: HarnessOptions | None = None,
) -> HarnessResult:
    if options is None:
        options = HarnessOptions()

    max_attempts = options.max_attempts
    latest_result: HarnessResult | None = None

    for attempt in range(1, max_attempts + 1):
        exec_result = await _run_harness_attempt(task, model)
        verification = options.verify(exec_result) if options.verify else None
        answer = verification.reason if (verification and not verification.passed) else exec_result.answer

        latest_result = HarnessResult(
            answer=answer,
            iterations=exec_result.iterations,
            trace=exec_result.trace,
            stopped_by=exec_result.stopped_by,
            task=exec_result.task,
            model=exec_result.model,
            attempts=attempt,
            verification=verification,
        )

        if not verification or verification.passed or verification.fatal or attempt == max_attempts:
            return latest_result

        print(f"\nAttempt {attempt} failed - retrying ({attempt + 1}/{max_attempts})...\n")

    raise RuntimeError("Harness finished without producing a result")


async def _run_harness_attempt(task: str, model: str) -> HarnessExecutionResult:
    session = BrowserSession()
    await session.open()
    try:
        tools = create_tools(session)
        messages = create_context(task)
        result = await run_loop(model, messages, tools, default_guardrails)
        return HarnessExecutionResult(
            answer=result.answer,
            iterations=result.iterations,
            trace=result.trace,
            stopped_by=result.stopped_by,
            task=task,
            model=model,
        )
    finally:
        await session.close()


def verify_successful_upvote(result: HarnessExecutionResult) -> VerifyResult:
    all_events = [event for iteration in result.trace for event in iteration.tool_events]

    successful_upvote = next(
        (
            event for event in all_events
            if event.tool == "browser_click"
            and re.search(r"up_", json.dumps(event.args))
            and re.search(
                r"news\.ycombinator\.com/(news)?$",
                event.result.split("now at ")[1].strip() if "now at " in event.result else "",
            )
        ),
        None,
    )

    if successful_upvote:
        url = successful_upvote.result.split("now at ")[1] if "now at " in successful_upvote.result else ""
        return VerifyResult(passed=True, reason=f"Upvote click confirmed - landed on {url}")

    failed_login = next(
        (
            event for event in all_events
            if event.tool == "harness_auto_login"
            and event.result.startswith("Harness failed to handle login at ")
        ),
        None,
    )

    if failed_login:
        return VerifyResult(passed=False, reason=failed_login.result, fatal=True)

    unrecovered_login = next(
        (
            event for event in all_events
            if event.tool != "harness_auto_login"
            and _is_login_url(_extract_url(event.result))
        ),
        None,
    )

    if unrecovered_login:
        url = _extract_url(unrecovered_login.result)
        return VerifyResult(
            passed=False,
            reason=f"Hit login screen instead of completing the upvote ({url})",
            fatal=True,
        )

    return VerifyResult(passed=False, reason="No successful upvote click found in trace")


def print_harness_result(result: HarnessResult) -> None:
    print("\n--- Agent trace ---\n")

    for iteration in result.trace:
        trim_note = " (trimmed)" if iteration.context_trimmed else ""
        ctx = f"[ctx: {iteration.context_size}{trim_note}]"

        if iteration.outcome == "tool_calls":
            print(f"[iter {iteration.index}] {len(iteration.tool_events)} tool call(s) {ctx}")
            for event in iteration.tool_events:
                print(f"  -> {event.tool}({json.dumps(event.args)})")
                truncated = event.result[:120] + ("..." if len(event.result) > 120 else "")
                print(f"     {truncated}")
        else:
            print(f"[iter {iteration.index}] answered {ctx}")

        print()

    print("--- Result ---\n")
    print(result.answer)
    print(f"\nStopped by: {result.stopped_by} after {result.iterations} iteration(s)")
    print(f"Attempts:   {result.attempts}")

    if result.verification:
        status = "PASS" if result.verification.passed else "FAIL"
        print(f"Verify:     {status} - {result.verification.reason}")


def _extract_url(result: str) -> str | None:
    match = re.search(r"https?://\S+", result)
    return match.group(0) if match else None


def _is_login_url(url: str | None) -> bool:
    return bool(url and ("/login" in url or "/vote" in url))
