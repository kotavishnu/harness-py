from dataclasses import dataclass
from typing import Callable


@dataclass
class GuardrailInput:
    iterations: int
    messages: list[dict]


@dataclass
class GuardrailResult:
    ok: bool
    reason: str = ""


GuardrailFn = Callable[[GuardrailInput], GuardrailResult]


def max_iterations(limit: int = 15) -> GuardrailFn:
    def check(input: GuardrailInput) -> GuardrailResult:
        if input.iterations >= limit:
            return GuardrailResult(ok=False, reason=f"Guardrail: reached iteration limit ({limit})")
        return GuardrailResult(ok=True)
    return check


def max_messages(limit: int = 50) -> GuardrailFn:
    def check(input: GuardrailInput) -> GuardrailResult:
        if len(input.messages) >= limit:
            return GuardrailResult(ok=False, reason=f"Guardrail: context too large ({limit} messages)")
        return GuardrailResult(ok=True)
    return check


def combine_guardrails(*fns: GuardrailFn) -> GuardrailFn:
    def check(input: GuardrailInput) -> GuardrailResult:
        for fn in fns:
            result = fn(input)
            if not result.ok:
                return result
        return GuardrailResult(ok=True)
    return check


default_guardrails = combine_guardrails(max_iterations(15), max_messages(50))
