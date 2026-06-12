import time
from dataclasses import dataclass
from .dataset import TestCase
from .scorers import ScorerFn
from .model import call_model


@dataclass
class RunResult:
    id: str
    expected: str
    actual: str
    trap: str | None
    fell_for_trap: bool
    score: float
    passed: bool
    latency_ms: int


@dataclass
class EvalRun:
    model: str
    results: list[RunResult]
    passed: int
    total: int
    avg_score: float
    avg_latency_ms: float


async def run_eval(cases: list[TestCase], model: str, scorer: ScorerFn) -> EvalRun:
    results: list[RunResult] = []

    for test_case in cases:
        start = time.monotonic()
        actual = await call_model(model, test_case.input)
        latency_ms = int((time.monotonic() - start) * 1000)
        score = scorer(actual, test_case.expected)

        fell_for_trap = (
            test_case.trap is not None
            and test_case.trap.lower() in actual.lower()
        )

        results.append(RunResult(
            id=test_case.id,
            expected=test_case.expected,
            actual=actual,
            trap=test_case.trap,
            fell_for_trap=fell_for_trap,
            score=score,
            passed=score >= 1.0,
            latency_ms=latency_ms,
        ))

    passed = sum(1 for r in results if r.passed)
    total = len(results)
    avg_score = sum(r.score for r in results) / total
    avg_latency_ms = sum(r.latency_ms for r in results) / total

    return EvalRun(
        model=model,
        results=results,
        passed=passed,
        total=total,
        avg_score=avg_score,
        avg_latency_ms=avg_latency_ms,
    )
