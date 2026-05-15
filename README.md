# AI Agents

AI agents built from scratch using the Anthropic Claude API — no frameworks, just raw SDK.

## Projects

### `0_basic_agent/`
A ReAct-style agent with weather, calculator, and Wikipedia tools.

**Tools:**
- `get_weather` — current weather via Open-Meteo (no API key needed)
- `calculate` — safe math expression evaluator
- `wikipedia_summary` — Wikipedia article summaries

**Run it:**
```bash
cd 0_basic_agent
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY="sk-ant-..."
python agent.py
```
