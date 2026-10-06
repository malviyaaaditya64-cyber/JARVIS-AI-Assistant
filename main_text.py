"""
JARVIS - Phase 1: Basic Text Chatbot (Google Gemini Version - FREE)
----------------------------------------------------------------------
Yeh Gemini free API use karta hai - koi credit card ya paid plan nahi chahiye.

Setup:
1. API key lo yaha se: https://aistudio.google.com/apikey
2. .env file mein likho: GEMINI_API_KEY=your_key_here
3. pip install -r requirements_gemini.txt
4. python main_text.py
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv

# .env file se API key load karo
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# JARVIS ki "personality"
SYSTEM_PROMPT = """You are JARVIS, a helpful and witty personal AI assistant.
Keep responses concise and clear. You can speak in Hindi-English mix (Hinglish)
if the user talks in Hinglish, otherwise match the user's language."""

# Model setup - gemini-1.5-flash free tier ke liye best hai (fast + generous limits)
model = genai.GenerativeModel(
    model_name="gemini-3.5-flash-lite",
    system_instruction=SYSTEM_PROMPT,
)

# Chat session banate hain - yeh automatically conversation history yaad rakhta hai
chat = model.start_chat(history=[])


def get_jarvis_response(user_input: str) -> str:
    """User ka message leke JARVIS (Gemini) se reply leta hai"""
    response = chat.send_message(user_input)
    return response.text


def main():
    print("=" * 50)
    print("JARVIS Online (Gemini). Type 'quit' to exit.")
    print("=" * 50)

    while True:
        user_input = input("\nYou: ")

        if user_input.lower() in ["quit", "exit", "bye"]:
            print("JARVIS: Goodbye, Sir/Ma'am!")
            break

        try:
            reply = get_jarvis_response(user_input)
            print(f"\nJARVIS: {reply}")
        except Exception as e:
            print(f"Error: {e}")
            print("Check your API key in .env file.")


if __name__ == "__main__":
    main()
