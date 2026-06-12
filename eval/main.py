import asyncio
from .dataset import dataset
from .scorers import score_contains
from .runner import run_eval, EvalRun

MODELS = [
    "ibm-granite/granite-4.0-h-micro",
    "anthropic/claude-haiku-4-5",
    "arcee-ai/trinity-large-preview:free",
]


def print_run(run: EvalRun) -> None:
    print(f"\n=== {run.model} ===\n")
    header = f"{'id':<30} {'pass':<6} {'trap':<6} {'expected':<12} {'actual':<20} {'ms':>6}"
    print(header)
    print("-" * len(header))
    for r in run.results:
        passed = "✓" if r.passed else "✗"
        trap = "🪤" if r.fell_for_trap else ""
        print(f"{r.id:<30} {passed:<6} {trap:<6} {r.expected:<12} {r.actual:<20} {r.latency_ms:>6}")


def print_comparison(runs: list[EvalRun]) -> None:
    print("\n=== COMPARISON ===\n")
    header = f"{'model':<45} {'passed':<10} {'traps':<7} {'avgScore':<10} {'avgLatencyMs':>12}"
    print(header)
    print("-" * len(header))
    for run in runs:
        traps = sum(1 for r in run.results if r.fell_for_trap)
        print(
            f"{run.model:<45} "
            f"{run.passed}/{run.total:<8} "
            f"{traps:<7} "
            f"{run.avg_score:.2f}{'':6} "
            f"{run.avg_latency_ms:>12.0f}"
        )


async def main():
    runs = await asyncio.gather(
        *[run_eval(dataset, model, score_contains) for model in MODELS]
    )
    for run in runs:
        print_run(run)
    print_comparison(list(runs))


if __name__ == "__main__":
    asyncio.run(main())
