from agent import Agent

agent = Agent()

print("Agent ready. Type 'reset' to clear memory, 'exit' to quit.\n")

while True:
    try:
        user_input = input("You: ").strip()
    except KeyboardInterrupt:
        break

    if not user_input:
        continue
    if user_input.lower() in ("exit", "quit"):
        break
    if user_input.lower() == "reset":
        agent.reset()
        continue

    agent.chat(user_input)
    print()
