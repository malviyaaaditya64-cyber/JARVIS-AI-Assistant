"""
JARVIS - Phase 3: Text Chatbot with Tools (Function Calling)
------------------------------------------------------------------
Ab JARVIS sirf baat hi nahi karega, balki KAAM bhi kar sakta hai:
- Weather check karna (kisi bhi city ka)
- Reminders add/list karna (local file mein save hote hain)
- Calculator (maths expressions solve karna)

Gemini khud decide karta hai kab kaunsa tool use karna hai - "automatic function calling"
ke through. Aapko manually kuch handle nahi karna.

Setup:
- pip install requests
- (google-generativeai, python-dotenv already installed hone chahiye)

Run: python main_text_tools.py
"""

import os
import json
import ast
import operator
from datetime import datetime
import requests
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

REMINDERS_FILE = "reminders.json"


# ============================================================
# TOOLS - yeh normal Python functions hain jo Gemini call karega
# Docstrings aur type hints IMPORTANT hain - Gemini isi se samajhta hai
# ki function kya karta hai aur kya arguments chahiye
# ============================================================

def get_weather(city: str) -> str:
    """Get the current weather for a given city name.

    Args:
        city: Name of the city, e.g. 'Bhopal' or 'Mumbai'
    """
    try:
        # Step 1: City ka naam se coordinates (lat/long) nikalo - free geocoding API
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
        geo_response = requests.get(geo_url, timeout=10).json()

        if not geo_response.get("results"):
            return f"'{city}' naam ka shehar nahi mila. Spelling check karo."

        location = geo_response["results"][0]
        lat, lon = location["latitude"], location["longitude"]
        found_name = location["name"]

        # Step 2: Un coordinates ka current weather nikalo - free forecast API
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,wind_speed_10m"
        weather_response = requests.get(weather_url, timeout=10).json()

        current = weather_response["current"]
        temp = current["temperature_2m"]
        humidity = current["relative_humidity_2m"]
        wind = current["wind_speed_10m"]

        return f"{found_name} mein abhi temperature {temp}°C hai, humidity {humidity}%, wind speed {wind} km/h."

    except Exception as e:
        return f"Weather fetch karne mein error aaya: {e}"


def add_reminder(task: str) -> str:
    """Add a new reminder or to-do item to the user's reminder list.

    Args:
        task: Description of the task to remember, e.g. 'Call mom at 5pm'
    """
    reminders = _load_reminders()
    reminders.append({
        "task": task,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    _save_reminders(reminders)
    return f"Reminder add ho gaya: '{task}'"


def list_reminders() -> str:
    """List all current reminders/to-do items the user has saved."""
    reminders = _load_reminders()
    if not reminders:
        return "Koi reminders nahi hain abhi."

    result = "Aapke reminders:\n"
    for i, r in enumerate(reminders, 1):
        result += f"{i}. {r['task']} (added: {r['created_at']})\n"
    return result


def calculate(expression: str) -> str:
    """Safely evaluate a mathematical expression and return the result.

    Args:
        expression: A math expression as a string, e.g. '15 * 8 + 20' or '(200-50)/3'
    """
    # Safe eval - sirf math operations allow karte hain, koi code execution nahi
    allowed_operators = {
        ast.Add: operator.add, ast.Sub: operator.sub,
        ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Pow: operator.pow, ast.USub: operator.neg,
        ast.Mod: operator.mod,
    }

    def eval_node(node):
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.BinOp):
            return allowed_operators[type(node.op)](eval_node(node.left), eval_node(node.right))
        elif isinstance(node, ast.UnaryOp):
            return allowed_operators[type(node.op)](eval_node(node.operand))
        else:
            raise ValueError("Invalid expression")

    try:
        tree = ast.parse(expression, mode="eval")
        result = eval_node(tree.body)
        return f"{expression} = {result}"
    except Exception as e:
        return f"Calculate nahi kar paya: {e}"


def _load_reminders() -> list:
    """Helper function - reminders.json file se list load karta hai"""
    if os.path.exists(REMINDERS_FILE):
        with open(REMINDERS_FILE, "r") as f:
            return json.load(f)
    return []


def _save_reminders(reminders: list):
    """Helper function - reminders list ko file mein save karta hai"""
    with open(REMINDERS_FILE, "w") as f:
        json.dump(reminders, f, indent=2)


# ============================================================
# MAIN CHATBOT SETUP
# ============================================================

SYSTEM_PROMPT = """You are JARVIS, a helpful personal AI assistant with access to tools:
weather check, reminders, and a calculator. Use tools when relevant to the user's request.
Keep responses concise. Match the user's language style (Hindi/English/Hinglish)."""

model = genai.GenerativeModel(
    model_name="gemini-3.5-flash-lite",
    system_instruction=SYSTEM_PROMPT,
    tools=[get_weather, add_reminder, list_reminders, calculate],
)

# enable_automatic_function_calling=True - Gemini khud tool call karega aur result use karega
chat = model.start_chat(enable_automatic_function_calling=True)


def main():
    print("=" * 55)
    print("JARVIS Online (with Tools). Type 'quit' to exit.")
    print("Available tools: Weather, Reminders, Calculator")
    print("=" * 55)

    while True:
        user_input = input("\nYou: ")

        if user_input.lower() in ["quit", "exit", "bye"]:
            print("JARVIS: Goodbye, Sir/Ma'am!")
            break

        try:
            response = chat.send_message(user_input)
            print(f"\nJARVIS: {response.text}")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()