# harness-py

A Python framework with two independent modules: an autonomous **browser agent** that uses LLMs with function calling to control a browser, and an **LLM evaluation suite** that benchmarks models on factual QA with deliberate trap answers.

---

## Project Layout

```
harness-py/
├── agent/          # Autonomous browser agent
│   ├── main.py     # Entry point — runs the agent task
│   ├── browser.py  # Playwright browser session wrapper
│   ├── context.py  # Initial message context builder
│   ├── model.py    # OpenRouter API client
│   ├── tools.py    # Tool definitions and registry
│   ├── loop.py     # Agent reasoning loop
│   └── guardrails.py
├── eval/           # LLM evaluation framework
│   ├── main.py     # Entry point — runs all model evals
│   ├── model.py    # OpenRouter API caller
│   ├── dataset.py  # Test cases with trap answers
│   ├── runner.py   # Per-model evaluation runner
│   └── scorers.py  # Scoring functions
├── requirements.txt
└── .env.example
```

---

## Setup

**Prerequisites:** Python 3.10+, a [OpenRouter](https://openrouter.ai) API key.

```bash
pip install -r requirements.txt
playwright install chromium

cp .env.example .env
# Edit .env and set OPENROUTER_API_KEY=sk-or-v1-...
```

---

## Agent Module

The agent uses a model-calls-tools loop to complete browser tasks autonomously.

### How it works

1. The agent is given a task as a natural language instruction.
2. The model receives the task and a set of browser tools.
3. The model emits tool calls; the loop executes them against a live Chromium browser.
4. Results are fed back to the model. The loop repeats until the model stops.

### Available tools

| Tool | Description |
|---|---|
| `browser_navigate` | Navigate to a URL |
| `browser_url` | Get current page URL |
| `browser_get_text` | Get visible page text (up to 4000 chars) |
| `browser_fill` | Fill an input field |
| `browser_click` | Click an element |
| `browser_get_stories` | Get structured Hacker News story list (rank, ID, title, voted status) |
| `browser_has_class` | Check whether an element has a CSS class |

### Running the agent

```bash
python -m agent.main
```

The default task upvotes a story on Hacker News using `gpt-3.5-turbo-0613` via OpenRouter.

### Key types (`agent/loop.py`)

```python
@dataclass
class LoopResult:
    answer: str | None       # Final model response
    iterations: int          # Number of reasoning turns
    trace: list[LoopIteration]
    stopped_by: str          # "model" when the model halts naturally
```

### Extending the agent

- **New tools:** Add a tool definition and executor to `agent/tools.py`.
- **New tasks:** Change the user message in `agent/main.py`.
- **Hooks:** Pass `ToolHooks(on_upvote_success=..., on_stories_loaded=...)` to `ToolRegistry` to observe specific events.

---

## Eval Module

Benchmarks multiple LLMs on a curated factual QA dataset. Each test case includes a known "trap" — a plausible but wrong answer — to measure whether the model avoids common misconceptions.

### Test dataset (`eval/dataset.py`)

| # | Question | Correct answer | Trap |
|---|---|---|---|
| 1 | Capital of Australia | Canberra | Sydney |
| 2 | Capital of Brazil | Brasília | Rio de Janeiro |
| 3 | Country with most lakes | Canada | Russia |
| 4 | Octopus hearts | 3 | 1 |
| 5 | Spider legs | 8 | 6 |
| 6 | Mars moons | 2 | 1 |
| 7 | Most populous country (2024) | India | China |
| 8 | Does salt lower boiling point? | No (raises it) | lower |

### Running evals

```bash
python -m eval.main
```

Output — per-model result table, then a side-by-side comparison:

```
Model                                Pass    Traps   Score   Latency
ibm-granite/granite-4.0-h-micro      7/8     0       0.94    312 ms
anthropic/claude-haiku-4-5           8/8     0       1.00    289 ms
arcee-ai/trinity-large-preview:free  6/8     1       0.79    541 ms
```

Models tested by default:

- `ibm-granite/granite-4.0-h-micro`
- `anthropic/claude-haiku-4-5`
- `arcee-ai/trinity-large-preview:free`

### Scoring functions (`eval/scorers.py`)

| Function | Returns |
|---|---|
| `score_exact_match` | `1.0` if normalized answer matches exactly |
| `score_contains` | `1.0` if expected is a substring of actual |
| `score_keywords` | Fraction of expected keywords found in actual |

Numbers written as words (`one`, `two`, …) are normalized to digits before comparison.

### Adding test cases

Add a `TestCase` to the list in `eval/dataset.py`:

```python
TestCase(
    id="geo-3",
    input="What is the capital of Japan?",
    expected="Tokyo",
    trap="Osaka",
    tags=["geography"],
)
```

---

## Environment Variables

| Variable | Description |
|---|---|
| `OPENROUTER_API_KEY` | API key from openrouter.ai — used by both modules |

---

## Dependencies

| Package | Purpose |
|---|---|
| `openai>=1.30.0` | AsyncOpenAI client (pointed at OpenRouter) |
| `playwright>=1.45.0` | Browser automation (agent module) |
| `python-dotenv>=1.0.0` | `.env` file loading |
