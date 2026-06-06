import anthropic
from tools import TOOLS, dispatch_tool

client = anthropic.Anthropic()

SYSTEM_PROMPT = """You are a helpful assistant with access to the following tools:

- get_weather: Get current weather conditions for any city.
- calculate: Evaluate math expressions (+, -, *, /, **, %).
- wikipedia_summary: Look up background information on any topic.

When answering questions:
1. Think about whether you can answer from knowledge or need a tool.
2. Use get_weather for any question about current weather or temperature.
3. Use calculate for any arithmetic or math the user asks you to compute.
4. Use wikipedia_summary for background info, definitions, or overviews of topics.
5. You can call multiple tools in sequence if needed.
6. Once you have enough information, give a clear, direct answer.
"""

MAX_ITERATIONS = 10

def run_agent(user_input: str):
    messages = [{"role": "user", "content": user_input}]

    for i in range(MAX_ITERATIONS):

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages
        )

        messages.append({"role": "assistant", "content": response.content})

        # Case 1: Claude is done — print the answer and exit
        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    print(f"\nAgent: {block.text}")
            return
        
        # Case 2: Claude wants to use a tool
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
            messages.append({"role": "user", "content": tool_results})
    
    print("\n[Max iterations reached]")

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