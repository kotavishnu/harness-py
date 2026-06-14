# harness-py

A framework for running and evaluating LLM agents that interact with web browsers to complete real-world tasks. Built on Playwright and OpenRouter.

## What it does

The project has two independent modules:

- **`agent/`** — A browser automation agent that uses an LLM to navigate websites and complete tasks. The current task is upvoting a story on Hacker News. The agent calls browser tools in a loop until it succeeds or hits a guardrail, with automatic retry and verification.
- **`eval/`** — A lightweight evaluation runner that tests multiple models against a fixed Q&A dataset, scoring answers and detecting "trap" responses (plausible-but-wrong answers).

## Project structure

```
harness-py/
├── agent/
│   ├── main.py           # Entry point — defines the task and runs the harness
│   ├── harness.py        # Orchestration, retry logic, result verification
│   ├── loop.py           # Core agent loop (model → tool calls → messages)
│   ├── browser.py        # Playwright session wrapper
│   ├── tools.py          # Tool definitions the model can call
│   ├── context.py        # Message history creation and trimming
│   ├── login_handler.py  # Auto-login for Hacker News when redirected
│   ├── guardrails.py     # Stop conditions (iteration limit, upvote success)
│   └── model.py          # OpenRouter API client setup
├── eval/
│   ├── main.py           # Entry point — runs models in parallel and prints comparison
│   ├── runner.py         # Evaluation loop per model
│   ├── dataset.py        # Test cases with expected answers and trap answers
│   ├── scorers.py        # Scoring functions (exact match, contains, keywords)
│   └── model.py          # Single model call via OpenRouter
├── .env.example
└── requirements.txt
```

## Setup

**1. Install dependencies**

```bash
pip install -r requirements.txt
playwright install chromium
```

**2. Set your API key**

```bash
cp .env.example .env
# Edit .env and set your OpenRouter API key
OPENROUTER_API_KEY=your_api_key_here
```

Get an API key at [openrouter.ai](https://openrouter.ai).

## Running

**Agent (Hacker News upvote task)**

```bash
python -m agent.main
```

Opens a Chromium browser, initializes an LLM agent, and has it navigate to Hacker News and upvote a story. The agent retries up to 3 times and verifies success after each attempt. Progress and tool calls are printed to stdout.

**Eval (model comparison)**

```bash
python -m eval.main
```

Tests 3 models (IBM Granite 4.0, Claude Haiku 4.5, Trinity Large) against 8 Q&A questions in parallel. Prints each model's answers with pass/fail status and a summary table showing pass rate, trap avoidance, average score, and latency.

## How the agent works

```
run_harness()
  └─ for each attempt (max 3):
       ├─ open browser
       ├─ build message context with the task
       └─ run_loop():
            ├─ trim context to 20 messages
            ├─ check guardrails (iterations, success)
            ├─ call model → tool_calls or stop
            ├─ execute browser tools (navigate, click, fill, get_text, ...)
            ├─ auto-login if redirected to login page
            └─ repeat until done
       └─ verify_successful_upvote()
```

**Browser tools available to the model:**

| Tool | Description |
|------|-------------|
| `browser_navigate` | Navigate to a URL |
| `browser_url` | Get current page URL |
| `browser_get_text` | Get visible page text (up to 4000 chars) |
| `browser_fill` | Fill an input field |
| `browser_click` | Click an element |
| `browser_get_stories` | Get structured HN story list (rank, title, vote status) |
| `browser_has_class` | Check if an element has a CSS class |

**Guardrails:** The agent stops if it exceeds 15 iterations, accumulates 50 messages, or successfully upvotes a story.

## How the eval works

Each test case has an `input` (a question), an `expected` answer, and an optional `trap` answer (a plausible wrong answer the model might give). Results are scored with `score_contains` — the expected answer must appear in the model's response. A run is flagged if the model's response contains the trap answer.

The dataset covers geography, biology, astronomy, chemistry, and current-events questions.

## Configuration

| Variable | Description |
|----------|-------------|
| `OPENROUTER_API_KEY` | Required. Your OpenRouter API key. |

To change the model used by the agent, edit `agent/main.py`. To change eval models, edit `eval/main.py`. To switch the browser to headed/headless mode, edit `headless=` in `agent/browser.py`.
