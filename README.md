# harness-py

An async Python framework with two subsystems: an LLM-driven browser agent harness and a structured model evaluation benchmark. The agent module lets any OpenRouter-accessible model control a real browser to complete web tasks; the eval module benchmarks model accuracy on factual QA with trap detection.

---

## Architecture

```
harness-py/
├── agent/               # LLM-controlled browser automation
│   ├── harness.py       # Orchestrator: retry logic + verification
│   ├── loop.py          # Agentic loop: model ↔ tool calls
│   ├── browser.py       # Playwright browser session wrapper
│   ├── tools.py         # Tool schemas + hook callbacks
│   ├── context.py       # System/user prompt + FIFO context trimming
│   ├── guardrails.py    # Composable iteration/message limits
│   ├── model.py         # OpenRouter async client
│   └── main.py          # Runnable demo (Hacker News upvote)
└── eval/                # LLM benchmarking
    ├── runner.py        # Concurrent test executor + result aggregation
    ├── dataset.py       # TestCase definitions with trap answers
    ├── scorers.py       # Scoring functions (exact, contains, keywords)
    ├── model.py         # Single-shot model caller
    └── main.py          # Runnable benchmark (3 models, 8 test cases)
```

The two modules are independent — `agent/` and `eval/` each have their own `model.py` and can be used separately.

---

## Setup

**Requirements:** Python 3.11+

```bash
pip install -r requirements.txt
playwright install chromium
```

Copy the env template and fill in your key:

```bash
cp .env.example .env
# edit .env: set OPENROUTER_API_KEY=<your key>
```

### Environment Variables

| Variable | Required | Description |
|---|---|---|
| `OPENROUTER_API_KEY` | Yes | API key from [openrouter.ai](https://openrouter.ai) |

---

## Running the Demos

**Agent** — runs a Hacker News upvote task end-to-end:

```bash
python -m agent.main
```

**Eval** — benchmarks Granite 4.0, Claude Haiku 4.5, and Trinity Large against 8 factual QA test cases:

```bash
python -m eval.main
```

---

## Key Concepts

### Agentic loop (`agent/loop.py`)

`run_loop()` iterates: call model with current message history → execute any tool calls the model requests → append results to history → repeat. The loop exits when the model returns a final text answer (no tool calls) or a guardrail fires.

### Trace-based verification (`agent/harness.py`)

`run_harness()` wraps the loop with optional verification. Success is determined by inspecting the complete trace of tool calls, not the model's reply text. If verification fails, the harness retries up to `HarnessOptions.max_attempts` times.

```python
from agent.harness import run_harness, HarnessOptions

result = await run_harness(
    task="...",
    options=HarnessOptions(max_attempts=3, verify=my_verify_fn),
)
```

A verify function receives the trace and returns a `VerifyResult(success=bool, message=str)`.

### Guardrails (`agent/guardrails.py`)

Composable safety predicates. The defaults cap execution at 15 iterations and 50 messages:

```python
from agent.guardrails import max_iterations, max_messages, combine_guardrails

guards = combine_guardrails(max_iterations(15), max_messages(50))
```

Add a guardrail by writing a function `(state) -> bool` and composing it in.

### Context trimming (`agent/context.py`)

When message history exceeds `MAX_CONTEXT_MESSAGES = 20`, `trim_context()` removes the oldest middle messages (FIFO). The system prompt and original user message are always preserved.

### OpenRouter client (`agent/model.py`, `eval/model.py`)

Both modules use the OpenAI SDK pointed at OpenRouter's base URL. Any model slug available on OpenRouter works — just change the model string passed to the API call.

---

## Extending the Agent

### Add a new task

```python
from agent.harness import run_harness, HarnessOptions
from agent.harness import VerifyResult

async def verify_fn(trace) -> VerifyResult:
    # inspect trace for success criteria
    return VerifyResult(success=True, message="done")

await run_harness(
    task="Go to example.com and click the signup button.",
    options=HarnessOptions(max_attempts=2, verify=verify_fn),
)
```

### Add a browser tool

1. Add an `async` method to `BrowserSession` in [agent/browser.py](agent/browser.py)
2. Add the tool schema and executor entry in [agent/tools.py](agent/tools.py)

The model will discover and call the new tool automatically — no changes to the loop needed.

### Add a hook

Hooks fire when the model calls a specific tool. Pass them to `create_tools()`:

```python
hooks = {
    "browser_click": my_async_callback,
}
```

---

## Extending the Eval

### Add test cases

Add `TestCase` entries to `DATASET` in [eval/dataset.py](eval/dataset.py):

```python
TestCase(
    id="geo_9",
    input="What is the capital of Japan?",
    expected="Tokyo",
    trap="Kyoto",  # common wrong answer the model should not say
    tags=["geography"],
)
```

### Add a scorer

Add a function to [eval/scorers.py](eval/scorers.py) with the signature:

```python
def score_my_method(expected: str, actual: str) -> float:
    ...  # return 0.0–1.0
```

Pass it as the `scorer` argument to `run_eval()`.

### Benchmark a new model

Add the OpenRouter model slug to the `MODELS` list in [eval/main.py](eval/main.py):

```python
MODELS = [
    "ibm/granite-4-dense",
    "anthropic/claude-haiku-4-5",
    "tngtech/deepseek-r1t-chimera:free",
    "your-provider/your-model",
]
```
