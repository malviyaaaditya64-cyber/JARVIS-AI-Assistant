"""
JARVIS - Phase 3: Voice-Enabled Chatbot with Tools
--------------------------------------------------------
Ab aap AWAAZ se JARVIS ko bol sakte ho weather check karne, reminders add karne,
ya calculations karne ke liye - aur JARVIS awaaz mein hi jawab dega.

Setup:
- pip install requests pyaudiowpatch speechrecognition pyttsx3
- (google-generativeai, python-dotenv already installed hone chahiye)

Run: python main_voice_tools.py
"""

import os
import sys
import json
import ast
import operator
from datetime import datetime
import requests
import pyaudiowpatch as pyaudio

sys.modules["pyaudio"] = pyaudio

import speech_recognition as sr
import pyttsx3
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

REMINDERS_FILE = "reminders.json"
recognizer = sr.Recognizer()


# ============================================================
# TOOLS - same functions jo text version mein the
# ============================================================

def get_weather(city: str) -> str:
    """Get the current weather for a given city name.

    Args:
        city: Name of the city, e.g. 'Bhopal' or 'Mumbai'
    """
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
        geo_response = requests.get(geo_url, timeout=10).json()

        if not geo_response.get("results"):
            return f"'{city}' naam ka shehar nahi mila. Spelling check karo."

        location = geo_response["results"][0]
        lat, lon = location["latitude"], location["longitude"]
        found_name = location["name"]

        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,wind_speed_10m"
        weather_response = requests.get(weather_url, timeout=10).json()

        current = weather_response["current"]
        temp = current["temperature_2m"]
        humidity = current["relative_humidity_2m"]
        wind = current["wind_speed_10m"]

        return f"{found_name} mein abhi temperature {temp} degree Celsius hai, humidity {humidity} percent, wind speed {wind} km per hour."

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
    return f"Reminder add ho gaya: {task}"


def list_reminders() -> str:
    """List all current reminders/to-do items the user has saved."""
    reminders = _load_reminders()
    if not reminders:
        return "Koi reminders nahi hain abhi."

    result = "Aapke reminders hain: "
    for i, r in enumerate(reminders, 1):
        result += f"{i}: {r['task']}. "
    return result


def calculate(expression: str) -> str:
    """Safely evaluate a mathematical expression and return the result.

    Args:
        expression: A math expression as a string, e.g. '15 * 8 + 20'
    """
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
        return f"Answer is {result}"
    except Exception as e:
        return f"Calculate nahi kar paya: {e}"


def _load_reminders() -> list:
    if os.path.exists(REMINDERS_FILE):
        with open(REMINDERS_FILE, "r") as f:
            return json.load(f)
    return []


def _save_reminders(reminders: list):
    with open(REMINDERS_FILE, "w") as f:
        json.dump(reminders, f, indent=2)


# ============================================================
# VOICE FUNCTIONS
# ============================================================

def speak(text: str):
    """JARVIS ko bolwane ke liye - har baar naya engine (Windows bug fix)"""
    print(f"JARVIS: {text}")
    local_engine = pyttsx3.init()
    local_engine.setProperty("rate", 175)
    local_engine.say(text)
    local_engine.runAndWait()
    local_engine.stop()


def listen() -> str:
    """Microphone se voice sunke text mein convert karta hai"""
    with sr.Microphone() as source:
        print("\nListening... (bolo)")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio, language="en-IN")
        print(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as e:
        print(f"Speech recognition error: {e}")
        return ""


# ============================================================
# MAIN SETUP
# ============================================================

SYSTEM_PROMPT = """You are JARVIS, a helpful personal AI assistant with access to tools:
weather check, reminders, and a calculator. Use tools when relevant.
Keep responses SHORT (1-3 sentences) since they will be spoken out loud.
Match the user's language style (Hindi/English/Hinglish)."""

model = genai.GenerativeModel(
    model_name="gemini-3.5-flash-lite",
    system_instruction=SYSTEM_PROMPT,
    tools=[get_weather, add_reminder, list_reminders, calculate],
)

chat = model.start_chat(enable_automatic_function_calling=True)


def main():
    speak("JARVIS online with tools ready. How can I help you?")

    while True:
        user_input = listen()

        if not user_input:
            continue

        if user_input.lower() in ["quit", "exit", "bye", "stop"]:
            speak("Goodbye!")
            break

        try:
            response = chat.send_message(user_input)
            speak(response.text)
        except Exception as e:
            print(f"Error: {e}")
            speak("Sorry, kuch error aa gaya.")


if __name__ == "__main__":
    main()