# Plan: Build a Simple AI Agent from Scratch (Python + Claude API)

## Context

Build a ReAct-style AI agent from scratch — no LangChain, no AutoGen, no frameworks.
Only the raw `anthropic` Python SDK. CLI chat loop, web search tool, loops until it can answer.

---

## File Structure

```
AIAgents/
└── 0_basic_agent/
    ├── .venv/            # Python virtual environment
    ├── agent.py          # Entry point + core ReAct loop
    ├── tools.py          # Tool schema (TOOLS list) + dispatch_tool()
    ├── search.py         # DuckDuckGo web search implementation
    ├── requirements.txt  # Dependencies
    └── PLAN.md           # This file
```

---

## Step 1 — `requirements.txt`

```
anthropic>=0.49.0
requests>=2.31.0
beautifulsoup4>=4.12.0
```

---

## Step 2 — `search.py`

POST to `https://html.duckduckgo.com/html/` with `q=<query>` and a realistic `User-Agent` header.
Parse `<a class="result__snippet">` elements with BeautifulSoup (`html.parser`).
Return top N results as a formatted string. On failure, return a descriptive error string.

**Signature:** `web_search(query: str, num_results: int = 5) -> str`

**Return format:**
```
Result 1: <title>
URL: <url>
Snippet: <snippet>

Result 2: ...
```

**Test standalone:**
```bash
python -c "from search import web_search; print(web_search('current gold price'))"
```

---

## Step 3 — `tools.py`

### `TOOLS` list (the JSON schema Claude sees)

```python
TOOLS = [
    {
        "name": "web_search",
        "description": "Search the web for current information. Use when you need up-to-date facts, recent events, or specific data not in your training data.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Specific, concise search query"
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of results to return (1-10). Default 5.",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    }
]
```

### `dispatch_tool()` function

```python
from search import web_search

def dispatch_tool(name: str, input_dict: dict) -> str:
    if name == "web_search":
        return web_search(input_dict["query"], input_dict.get("num_results", 5))
    return f"Unknown tool: {name}"
```

To add a new tool later: add entry to `TOOLS` + add a branch in `dispatch_tool`.

---

## Step 4 — `agent.py`

### System prompt + prompt caching

Pass `system` as a list of blocks (not a plain string) to enable caching:

```python
SYSTEM_PROMPT = """You are a helpful research assistant with access to a web search tool.

When answering questions:
1. Think about whether you need current information or can answer from knowledge.
2. Use web_search when you need up-to-date facts, recent events, or specific data.
3. You can call search multiple times with different queries.
4. Once you have enough information, synthesize a clear, direct answer.
5. Always cite your sources by mentioning URLs from search results."""

system = [
    {
        "type": "text",
        "text": SYSTEM_PROMPT,
        "cache_control": {"type": "ephemeral"}  # caches tools+system after first call
    }
]
```

### ReAct loop

```python
MAX_ITERATIONS = 10

def run_agent(user_input: str):
    messages = [{"role": "user", "content": user_input}]

    for i in range(MAX_ITERATIONS):
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=system,
            tools=TOOLS,
            messages=messages,
        )

        # Always append the FULL content list (tool_use blocks must be preserved)
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    print(f"\nAgent: {block.text}")
            return

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"\n[Calling: {block.name}({block.input})]")
                    result = dispatch_tool(block.name, block.input)
                    print(f"[Result: {result[:200]}...]")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,   # must match the tool_use block id exactly
                        "content": result
                    })
            messages.append({"role": "user", "content": tool_results})

    print("\n[Max iterations reached]")
```

**Key rules:**
- Append `response.content` (the full list) to the assistant turn — never just the text.
- `tool_use_id` must exactly match `block.id` from the assistant turn.
- All tool results for one round go into a single `user` turn.
- `stop_reason == "end_turn"` with no tool_use blocks = done.

### CLI loop

```python
import anthropic
from tools import TOOLS, dispatch_tool

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

if __name__ == "__main__":
    print("Agent ready. Type 'exit' to quit.\n")
    while True:
        try:
            user_input = input("You: ").strip()
        except KeyboardInterrupt:
            break
        if not user_input or user_input.lower() in ("exit", "quit"):
            break
        run_agent(user_input)
        print()
```

Each goal is stateless — fresh `messages` list per query.

---

## Step 5 — Error handling to add

| Scenario | What to do |
|---|---|
| `requests.Timeout` in search | Return `"Search timed out."` |
| No results from DuckDuckGo | Return `"No results found."` |
| `anthropic.RateLimitError` | `time.sleep(retry_after)`, retry once |
| `anthropic.APIStatusError` | Print error, return |
| Max iterations hit | Print warning, return |
| `KeyboardInterrupt` | Break the CLI loop cleanly |

---

## Running it

```bash
cd ~/Desktop/AIAgents/0_basic_agent
source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY="sk-ant-..."
python agent.py
```

## Test cases

1. `"What is the capital of France?"` — should answer without calling web_search
2. `"What happened in the news today?"` — should call web_search once
3. `"Who is the current CEO of OpenAI and what's their background?"` — may search twice
4. `exit` — should quit cleanly

## Verify caching is working

Add temporarily:
```python
print(f"Cache tokens: {response.usage.cache_read_input_tokens}")
```
On the second query it should be non-zero.
