from weather import get_weather
from calculator import calculate
from wikipedia import wikipedia_summary

TOOLS = [
    {
        "name": "get_weather",
        "description": "Get current weather conditions for a city. Returns temperature, humidity, wind speed, and weather code. Use this whenever the user asks about weather, temperature, or conditions in a specific location.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name, optionally with country (e.g., 'Tokyo', 'Paris, France', 'San Francisco, CA')"
                }
            },
            "required": ["city"]
        }
    },
    {
        "name": "calculate",
        "description": "Evaluate a mathematical expression. Supports +, -, *, /, ** (power), % (modulo). Use for any arithmetic the user asks you to compute.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Math expression to evaluate, e.g. '2 + 2', '(10 * 3) / 4', '2 ** 10'"
                }
            },
            "required": ["expression"]
        }
    },
    {
        "name": "wikipedia_summary",
        "description": "Fetch a summary of a topic from Wikipedia. Use when the user wants background information, definitions, or an overview of a person, place, concept, or event.",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The topic to look up, e.g. 'Python programming language', 'Eiffel Tower', 'Alan Turing'"
                }
            },
            "required": ["topic"]
        }
    }
]

def dispatch_tool(name: str, input_dict: dict) -> str:
    if name == "get_weather":
        return get_weather(input_dict["city"])
    if name == "calculate":
        return calculate(input_dict["expression"])
    if name == "wikipedia_summary":
        return wikipedia_summary(input_dict["topic"])
    return f"Unknown tool: {name}"
