# Code Explanation: What You Built and What to Learn From It

This document explains the AI agent you built in `0_basic_agent/`, line by line, and lists the key concepts worth learning from it.

---

## The Big Picture

You built a **ReAct agent** — a loop where an LLM:
1. **Reasons** about what to do
2. **Acts** by calling a tool
3. **Observes** the result
4. Repeats until it has enough to answer, until MAX_ITERATIONS

No framework does this for you here. You wrote the loop yourself. That's the whole point.

---

## Important Files Explanation

### `tools.py` — The Tool Registry

```python
TOOLS = [
    {
        "name": "get_weather",
        "description": "Get current weather conditions for a city...",
        "input_schema": { ... }
    }
]
```

`TOOLS` is a list of JSON schemas you pass to Claude. This is how Claude **knows a tool exists** and **what arguments to pass**.

The `input_schema` is standard **JSON Schema** — the same format used in REST APIs. Claude uses it to decide what arguments to construct when calling a tool.

```python
def dispatch_tool(name: str, input_dict: dict) -> str:
    if name == "get_weather":
        return get_weather(input_dict["city"])
    return f"Unknown tool: {name}"
```

`dispatch_tool` is a **router**. When Claude says "call `get_weather` with `{city: 'Tokyo'}`", this function receives that and calls the actual Python function. It's the bridge between Claude's intent and calling the tools.

---

### `agent.py` — The Core Loop


#### The `messages` List — The Memory

```python
messages = [{"role": "user", "content": user_input}]
```

This list **is** the agent's memory for one conversation turn. Every time you call the API, you send the full history. Claude has no memory of its own — you maintain it. We have up to 10 calls to get to our final answer,
10 because of MAX_ITERATIONS. 

Example: "What's the weather in Tokyo?"
Iteration 1 (i=0):
messages going in:
[
  {role: user, content: "What's the weather in Tokyo?"}
]
Send to Claude. Claude looks at this and thinks: "I need the weather tool." It responds with a tool_use block.
response.content looks like:
[
  ToolUseBlock(id="abc123", name="get_weather", input={"city": "Tokyo"})
]
response.stop_reason = "tool_use"
Now your code:

Appends Claude's response to messages (so Claude can see it next turn)
Sees stop_reason is "tool_use" — enters the tool branch
Runs get_weather("Tokyo") — gets back "Temperature: 18°C, Humidity: 65%..."
Appends the tool result to messages

messages now looks like:
[
  {role: user, content: "What's the weather in Tokyo?"},
  {role: assistant, content: [ToolUseBlock(id="abc123", name="get_weather", input={"city": "Tokyo"})]},
  {role: user, content: [{type: "tool_result", tool_use_id: "abc123", content: "Temperature: 18°C..."}]}
]
Loop continues. Claude hasn't given a final answer yet.

Iteration 2 (i=1):
Send the updated messages list back to Claude. Claude now sees:

The original question
Its own previous decision to call the tool
The tool's result

Claude thinks: "I have the data. Time to answer." Responds with text.
response.content looks like:
[
  TextBlock(text="The weather in Tokyo is currently 18°C with 65% humidity...")
]
response.stop_reason = "end_turn"
Your code:

Appends the response to messages
Sees stop_reason is "end_turn" — enters the done branch
Prints the text
return — exits the function

Done. Two iterations. Two API calls.
---

#### The API Call

```python
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=4096,
    system=SYSTEM_PROMPT,
    tools=TOOLS,
    messages=messages
)
```

- `model` — which Claude to use
- `max_tokens` — max length of Claude's response
- `system` — the system prompt (constant instructions)
- `tools` — the tool schemas (what Claude can call)
- `messages` — the conversation history

---

#### `stop_reason` — How Claude Signals What Happens Next

```python
if response.stop_reason == "end_turn":
    # Claude is done, print the answer

if response.stop_reason == "tool_use":
    # Claude wants to call a tool
```

`stop_reason` is how Claude communicates intent back to you:
- `"end_turn"` → Claude has a final answer, stop the loop
- `"tool_use"` → Claude needs to call one or more tools, continue the loop

This is the **decision branch** at the heart of every agent loop.

---

#### Dispatching Tools and Collecting Results

```python
for block in response.content:
    if block.type == "tool_use":
        result = dispatch_tool(block.name, block.input)
        tool_results.append({
            "type": "tool_result",
            "tool_use_id": block.id,   # ← must match the tool_use block's id
            "content": str(result)
        })
messages.append({"role": "user", "content": tool_results})
```

For each tool Claude wants to call:
1. You call `dispatch_tool` — your router that calls the real Python function
2. You wrap the result in a `tool_result` dict with the matching `id`
3. All tool results go into one `user` turn (even if Claude called multiple tools)

Claude then reads these results and decides what to do next.

---

## Key Concepts to Learn

### 1. The Messages API (Conversation Protocol)
The Anthropic Messages API is a **turn-based conversation protocol**. You send a list of turns, Claude responds with one turn. The conversation history is your responsibility — Claude is stateless.

**Learn:** How the `messages` array is structured. Why you must keep `tool_use` blocks in history.

### 2. Tool Use (Function Calling)
Claude doesn't call functions directly. It **describes** what it wants to call (name + arguments as JSON), and you execute it. This is intentional — it keeps the LLM sandboxed.

**Learn:** JSON Schema for defining tool inputs. The `tool_use` / `tool_result` round-trip pattern.

### 3. The ReAct Pattern
Reason + Act is the foundation of almost every useful agent. The loop continues until the model decides it has enough information (`end_turn`).

**Learn:** Why agents loop. What happens if you don't set `MAX_ITERATIONS`. How multi-hop reasoning works (Claude calls tool → sees result → calls another tool).

### 4. `stop_reason` as Control Flow
The `stop_reason` field is how Claude hands control back to you. Reading it correctly is the agent loop's core logic.

**Learn:** All possible `stop_reason` values (`end_turn`, `tool_use`, `max_tokens`, `stop_sequence`).

### 5. System Prompts
The system prompt shapes Claude's entire behaviour. Better prompts = smarter agents.

**Learn:** How to write effective system prompts. The difference between system prompt and user message. How to instruct Claude to use (or not use) tools.

### 6. External APIs Without Auth
`weather.py` calls Open-Meteo — no API key, no rate limits for small usage. A two-step pattern: geocode city → fetch weather.

**Learn:** How to find and use free APIs. The geocoding pattern (name → coordinates → data).

### 7. Separation of Concerns
- `weather.py` — knows nothing about Claude
- `tools.py` — knows about Claude's schema, routes calls
- `agent.py` — knows about the loop, knows nothing about weather

**Learn:** Why this separation makes it easy to add new tools. How to scale from 1 tool to 10.

---

## What to Build Next

| Extension | What You'll Learn |
|---|---|
| Add a web search tool | HTTP scraping, BeautifulSoup |
| Add a calculator tool | How simple tools work, `eval()` safely |
| Add conversation memory | Keeping `messages` across queries |
| Add prompt caching | `cache_control` blocks, cost reduction |
| Add error handling | `try/except` around API calls and tools |
| Stream the response | `client.messages.stream()`, streaming UX |
| Add a second agent | Multi-agent patterns, agent-as-tool |
