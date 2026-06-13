import json
import sys
from dataclasses import dataclass, field
from typing import Callable, Awaitable, Literal
from .model import client
from .tools import ToolRegistry
from .context import trim_context
from .guardrails import GuardrailFn, GuardrailInput, default_guardrails

MAX_CONTEXT_MESSAGES = 20


@dataclass
class ToolEvent:
    tool: str
    args: dict
    result: str


@dataclass
class LoopIteration:
    index: int
    outcome: Literal["tool_calls", "answer"]
    tool_events: list[ToolEvent]
    context_size: int
    context_trimmed: bool


@dataclass
class LoopResult:
    answer: str
    iterations: int
    trace: list[LoopIteration]
    stopped_by: Literal["model", "guardrail", "success"]


LoginHandler = Callable[[], Awaitable["ToolEvent | None"]]


async def run_loop(
    model: str,
    messages: list[dict],
    guardrail: GuardrailFn,
    tools: ToolRegistry,
    login_handler: LoginHandler | None = None,
) -> LoopResult:
    trace: list[LoopIteration] = []

    while True:
        iteration_index = len(trace) + 1

        before = len(messages)
        messages = trim_context(messages, MAX_CONTEXT_MESSAGES)
        context_trimmed = len(messages) < before

        check = guardrail(GuardrailInput(iterations=len(trace), messages=messages))
        if not check.ok:
            stopped_by = "success" if check.reason.startswith("Successfully") else "guardrail"
            return LoopResult(
                answer=check.reason,
                iterations=len(trace),
                trace=trace,
                stopped_by=stopped_by,
            )

        sys.stdout.write(f"[iter {iteration_index}] calling model... ")
        sys.stdout.flush()
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools.definitions,
        )

        choice = response.choices[0]
        context_size = len(messages)
        print(choice.finish_reason)

        messages.append(choice.message.model_dump(exclude_unset=False))

        if choice.finish_reason == "stop":
            trace.append(LoopIteration(
                index=iteration_index,
                outcome="answer",
                tool_events=[],
                context_size=context_size,
                context_trimmed=context_trimmed,
            ))
            return LoopResult(
                answer=choice.message.content or "(no response)",
                iterations=len(trace),
                trace=trace,
                stopped_by="model",
            )

        if choice.finish_reason == "tool_calls":
            tool_events: list[ToolEvent] = []

            for call in choice.message.tool_calls or []:
                name = call.function.name
                args = json.loads(call.function.arguments)

                tool = tools.by_name.get(name)
                sys.stdout.write(f"           → {name}({json.dumps(args)}) ... ")
                sys.stdout.flush()
                try:
                    result = await tool.execute(args) if tool else f'Unknown tool: "{name}"'
                    print("done")
                except Exception as err:
                    result = f"Error: {err}"
                    print("error")

                tool_events.append(ToolEvent(tool=name, args=args, result=result))
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": result,
                })

            if login_handler:
                login_event = await login_handler()
                if login_event:
                    tool_events.append(login_event)
                    messages.append({
                        "role": "user",
                        "content": "Authentication completed by harness. You are now logged in. Navigate back to https://news.ycombinator.com and complete your upvote task.",
                    })

            trace.append(LoopIteration(
                index=iteration_index,
                outcome="tool_calls",
                tool_events=tool_events,
                context_size=context_size,
                context_trimmed=context_trimmed,
            ))
