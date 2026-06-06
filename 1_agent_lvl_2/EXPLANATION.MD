# Level 2 Agent — Persistent Conversation Memory

## What's New vs Level 1

Level 1's `run_agent` was a plain function. Every call started with a fresh `messages = []`, so two consecutive prompts had no awareness of each other.

Level 2 wraps the agent in a **class**. The history lives on the object and accumulates across every call.

---

## The Core Upgrade: `self.history`

```python
class Agent:
    def __init__(self):
        self.history = []
```

`self.history` is the same messages list as level 1 — but now it's an instance variable, not a local variable. It survives between calls.

```python
def chat(self, user_input: str):
    self.history.append({"role": "user", "content": user_input})
```

Instead of creating a new list, we **append** to the existing one. By the third message, `self.history` looks like:

```
[
  {role: user,      content: "What is the weather in Tokyo?"},
  {role: assistant, content: [...]},
  {role: user,      content: [{type: tool_result, ...}]},
  {role: assistant, content: [TextBlock("It is 14°C...")]},
  {role: user,      content: "What was the temperature?"},   ← new message
]
```

Claude receives the full history every API call, so it can answer "What was the temperature?" correctly — it can see it already fetched that data.

---

## Separation of Concerns: `agent.py` vs `main.py`

Level 1 had the REPL loop inside `agent.py` under `if __name__ == "__main__"`. Level 2 splits this:

- **`agent.py`** — the `Agent` class only. No input(), no print() for the REPL. Pure logic.
- **`main.py`** — creates one `Agent` instance, runs the input loop, handles `reset`/`exit` commands.

This matters because `agent.py` can now be imported and used by anything — a web server, a test suite, another agent — without dragging in the REPL.

## Key Concepts

### 1. Stateful Object vs Stateless Function
A function forgets everything when it returns. An object retains state between method calls. Wrapping the agent in a class is what enables multi-turn memory — the history accumulates on `self` rather than disappearing on `return`.

### 2. History Growth
`self.history` grows with every turn. After many messages it will approach Claude's context window limit (~200k tokens for claude-sonnet-4-6). In a production agent you'd need to summarize or truncate old messages. That's a level 3 problem.
