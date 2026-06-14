# harness-py

Python implementation of an AI agent harness — infrastructure for tool-calling LLM agents and model evaluation.

## Overview

This project implements two complementary harness systems:

- **Agent Harness** (`agent/`) — runs a tool-calling loop where an LLM can browse the web, click elements, and navigate pages to complete a real task. The demo task: upvote a story on Hacker News.
- **Eval Harness** (`eval/`) — scores multiple models against a fixed dataset of questions designed with trap answers, measuring accuracy, hallucination rate, and latency.

Both systems are ported from a TypeScript reference implementation in `ref_repo/basically-ai-harness/`. Comparing the two repos side-by-side is a good way to understand the architectural decisions.

---

## Architecture

```
agent/
  main.py        task entry point — opens browser, wires everything together
    └── loop.py        core agent loop (call model → dispatch tools → repeat)
          ├── model.py       AsyncOpenAI client → OpenRouter
          ├── tools.py       tool registry (JSON schemas + handlers)
          │     └── browser.py   Playwright wrapper (navigate, click, extract)
          ├── context.py     build and trim the message list
          └── guardrails.py  composable safety checks (iteration/message limits)

eval/
  main.py        evaluation entry point — runs all models, prints comparison
    └── runner.py      eval loop (call model → score → record result)
          ├── model.py       thin OpenRouter API wrapper
          ├── dataset.py     TestCase list with known answers and trap values
          └── scorers.py     exact_match, contains, keywords scorers
```

---

## Prerequisites

- Python 3.10+
- An [OpenRouter](https://openrouter.ai) API key
- Chromium (installed via Playwright in setup below)

---

## Setup

```bash
cd harness-py
cp .env.example .env          # then add your OPENROUTER_API_KEY inside
pip install -r requirements.txt
playwright install chromium
```

`.env` needs one variable:

| Variable | Description |
|---|---|
| `OPENROUTER_API_KEY` | Required — get one at openrouter.ai |

---

## Running

### Agent Demo

```bash
python -m agent.main
```

Opens a Chromium browser, navigates to Hacker News, identifies the first unvoted story, and upvotes it. Each iteration prints the tool calls the model made, and the final answer confirms success.

### Eval Runner

```bash
python -m eval.main
```

Tests 3 models across 8 curated questions. Each question has a known correct answer and a common trap answer. Output is a per-model result table followed by a side-by-side comparison showing pass rate, trap-fall count, average score, and average latency.

---

## Module Reference

### Agent (`agent/`)

| Module | Responsibility |
|---|---|
| `main.py` | Entry point — opens BrowserSession, builds tool registry, runs loop |
| `loop.py` | Core agent loop: calls model, dispatches tool calls, checks guardrails, trims context |
| `tools.py` | Tool registry: JSON schema definitions and async handlers, bound to a BrowserSession |
| `browser.py` | Playwright BrowserSession wrapper — navigate, get text, parse stories, click, fill |
| `context.py` | `create_context(task)` and `trim_context(messages, max)` — keeps system + initial user message |
| `guardrails.py` | `max_iterations(n)`, `max_messages(n)`, `combine_guardrails(*fns)` |
| `model.py` | AsyncOpenAI client configured for OpenRouter base URL |

### Eval (`eval/`)

| Module | Responsibility |
|---|---|
| `main.py` | Entry point — iterates models, calls runner, prints tables |
| `runner.py` | `run_eval(model, dataset)` → list of RunResult (passed, fell_for_trap, score, latency_ms) |
| `dataset.py` | 8 TestCases: prompt, expected answer, trap value, scorer function |
| `scorers.py` | `score_exact_match`, `score_contains`, `score_keywords` — all normalise number words |
| `model.py` | `call_model(model_id, prompt)` → raw string response |

---

## Key Design Decisions

**Harness owns the environment.**
The `BrowserSession` is opened and closed by `main.py`, not by individual tools. Tools receive a bound session — they cannot outlive the harness.

**Tools are session-bound, not global.**
`tools.py` exposes `create_tools(session)` rather than a static list. This makes each run isolated and testable.

**Context trimming preserves the anchor.**
`trim_context` always keeps the system prompt and the first user message. Everything beyond `max=20` messages is dropped from the middle to prevent context rot from accumulating tool results.

**Guardrails are composable functions.**
Each guardrail is `(messages, iteration) -> GuardrailResult`. Combine them with `combine_guardrails(max_iterations(15), max_messages(50))`. Adding a new safety check does not require modifying the loop.

**Async throughout.**
All I/O — browser operations and model calls — is async. Do not introduce blocking calls.

---

## Extending the Agent

### Adding a tool

1. Implement the async function in `browser.py` (or a new module).
2. In `tools.py`, add an entry to the JSON schema list and a matching branch in the handler dispatch.
3. The loop in `loop.py` picks it up automatically — no other changes needed.

### Changing the model

Edit the model string passed in `agent/main.py`. Any OpenRouter model ID works, e.g. `anthropic/claude-haiku-4-5`.

### Adding a guardrail

Write a function with signature `(messages: list, iteration: int) -> GuardrailResult` in `guardrails.py`, then include it in the `combine_guardrails(...)` call in `main.py`.

---

## Extending the Eval

### Adding a test case

Append a `TestCase(prompt, expected, trap, scorer)` to the list in `eval/dataset.py`.

### Adding a model

Append its OpenRouter model ID to the `MODELS` list in `eval/main.py`.

### Adding a scorer

Add a function `(actual: str, expected: str) -> float` to `eval/scorers.py` and reference it from the relevant TestCase in `dataset.py`.

---

## Reference Implementation

`ref_repo/basically-ai-harness/` is the original TypeScript harness this project mirrors. The file numbering there (1-agent-tools, 2-agent-model, ...) maps directly to the module structure here. It is useful for understanding the design intent when the Python code is ambiguous.
