"""
JARVIS - Phase 2: Voice-Enabled Assistant (Google Gemini Version - FREE)
----------------------------------------------------------------------------
Ab JARVIS aapki awaaz sunega (speech-to-text) aur bolke jawab dega (text-to-speech).
Yeh Gemini free API use karta hai.

Extra Setup (voice ke liye):
- Windows: pip install pyaudio (error aaye to alag se solve karenge)
- Mac: brew install portaudio, phir pip install pyaudio
- Linux: sudo apt-get install python3-pyaudio

Run: python main_voice.py
"""

import os
import sys
import pyaudiowpatch as pyaudio

# Trick: speech_recognition internally karta hai "import pyaudio".
# Hum pehle hi sys.modules mein pyaudiowpatch ko "pyaudio" naam se register kar dete hain,
# taaki speech_recognition usi ko use kare bina kisi extra argument ke.
sys.modules["pyaudio"] = pyaudio

import speech_recognition as sr
import pyttsx3
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Speech recognizer setup
recognizer = sr.Recognizer()

SYSTEM_PROMPT = """You are JARVIS, a helpful personal AI assistant.
Keep responses SHORT (1-3 sentences) since they will be spoken out loud.
Match the user's language style (Hindi/English/Hinglish)."""

model = genai.GenerativeModel(
    model_name="gemini-3.5-flash-lite",
    system_instruction=SYSTEM_PROMPT,
)
chat = model.start_chat(history=[])


def speak(text: str):
    """JARVIS ko bolwane ke liye - har baar naya engine banate hain
    kyunki Windows pe same engine reuse karne se dusri baar se awaaz nahi aati (known bug)"""
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


def get_jarvis_response(user_input: str) -> str:
    response = chat.send_message(user_input)
    return response.text


def main():
    speak("JARVIS online. How can I help you?")

    while True:
        user_input = listen()

        if not user_input:
            continue

        if user_input.lower() in ["quit", "exit", "bye", "stop"]:
            speak("Goodbye!")
            break

        try:
            reply = get_jarvis_response(user_input)
            speak(reply)
        except Exception as e:
            print(f"Error: {e}")
            speak("Sorry, something went wrong.")


if __name__ == "__main__":
    main()
