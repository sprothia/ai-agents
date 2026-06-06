import anthropic
from tools import TOOLS, dispatch_tool

client = anthropic.Anthropic()

SYSTEM_PROMPT = """You are a helpful assistant with access to the following tools:

- get_weather: Get current weather conditions for any city.
- calculate: Evaluate math expressions (+, -, *, /, **, %).
- wikipedia_summary: Look up background information on any topic.

When answering questions:
1. Think about whether you can answer with or without needing a tool. Remember, you don't have to use the tools to answer.
2. Use get_weather for any question about current weather or temperature.
3. Use calculate for any arithmetic or math the user asks you to compute.
4. Use wikipedia_summary for background info, definitions, or overviews of topics.
5. You can call multiple tools in sequence if needed.
6. Once you have enough information, give a clear, direct answer.
"""

MAX_ITERATIONS = 10


class Agent:
    def __init__(self):
        self.history = []

    def _count_tokens(self):
        response = client.messages.count_tokens(
            model="claude-sonnet-4-6",
            system=SYSTEM_PROMPT,
            messages=self.history
        )

        return response.input_tokens
    
    def _maybe_summarize(self):
        token_count = self._count_tokens()
        if token_count > 1000:
            print("compacting")

            def serialize(content):
                if isinstance(content, str):
                    return content
                if isinstance(content, list):
                    parts = []
                    for block in content:
                        if hasattr(block, "text"):
                            parts.append(block.text)
                        elif isinstance(block, dict):
                            parts.append(str(block.get("content", "")))
                    return " ".join(parts)
                return str(content)

            history_text = "\n".join(
                f"{m['role'].upper()}: {serialize(m['content'])}"
                for m in self.history
            )

            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": f"Summarize this conversation concisely, preserving all key facts, questions, and answers:\n\n{history_text}"
                }]
            )

            summary_text = response.content[0].text

            self.history.clear();
            self.history.append({"role": "user",
                                 "content": f"Previous conversation summary: {summary_text}"})

            print(f"History is now: {self.history}")

    def reset(self):
        self.history = []
        print("[Memory cleared]")

    def chat(self, user_input: str):
        self.history.append({"role": "user", "content": user_input})

        for _ in range(MAX_ITERATIONS):

            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=self.history
            )

            self.history.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                self._maybe_summarize()
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
                        print(f"[Result: {str(result)[:200]}...]")
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": str(result)
                        })
                self.history.append({"role": "user", "content": tool_results})

        print("\n[Max iterations reached]")
