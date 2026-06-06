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

## Key Concepts to Learn

### 1. The Messages API (Conversation Protocol)
The Anthropic Messages API is a **turn-based conversation protocol**. You send a list of turns, Claude responds with one turn. The conversation history is your responsibility — Claude is stateless.

### 4. `stop_reason` as Control Flow
The `stop_reason` field is how Claude hands control back to you. Reading it correctly is the agent loop's core logic.

**Learn:** All possible `stop_reason` values (`end_turn`, `tool_use`, `max_tokens`, `stop_sequence`).