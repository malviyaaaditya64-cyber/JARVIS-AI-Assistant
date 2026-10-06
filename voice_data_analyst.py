"""
JARVIS - Voice-Enabled Data Analyst
----------------------------------------
Yeh CSV/Excel data ke baare mein AWAAZ se questions poochne deta hai,
aur JARVIS awaaz mein hi jawab deta hai.

Setup: main_voice.py aur data_analyst.py ke sab packages already installed hone chahiye
(pandas, openpyxl, pyaudiowpatch, speechrecognition, pyttsx3, google-generativeai)

Run: python voice_data_analyst.py
"""

import os
import sys
import re
import pandas as pd
import pyaudiowpatch as pyaudio

sys.modules["pyaudio"] = pyaudio

import speech_recognition as sr
import pyttsx3
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel(model_name="gemini-3.5-flash-lite")
recognizer = sr.Recognizer()


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


def load_file(path: str) -> pd.DataFrame:
    if path.endswith(".csv"):
        try:
            return pd.read_csv(path)
        except UnicodeDecodeError:
            return pd.read_csv(path, encoding="latin1")
    elif path.endswith((".xlsx", ".xls")):
        excel_file = pd.ExcelFile(path)
        if len(excel_file.sheet_names) > 1:
            print(f"Multiple sheets mile: {excel_file.sheet_names}")
            sheet = input(f"Kaunsi sheet use karni hai? (default: {excel_file.sheet_names[0]}): ").strip()
            sheet = sheet if sheet else excel_file.sheet_names[0]
            return pd.read_excel(path, sheet_name=sheet)
        return pd.read_excel(path)
    else:
        raise ValueError("Sirf .csv, .xlsx, ya .xls files supported hain")


def build_schema_context(df: pd.DataFrame) -> str:
    schema = f"Columns and types:\n{df.dtypes.to_string()}\n\n"
    schema += f"Shape: {df.shape[0]} rows, {df.shape[1]} columns\n\n"
    schema += f"First 3 rows (sample):\n{df.head(3).to_string()}\n"
    return schema


def extract_code(response_text: str) -> str:
    match = re.search(r"```(?:python)?\s*(.*?)```", response_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return response_text.strip()


def generate_and_run_code(df: pd.DataFrame, question: str, schema_context: str, previous_error: str = None, previous_code: str = None) -> tuple:
    """Ek attempt mein code generate karke run karta hai. Returns (success, result_or_error, code)"""

    if previous_error:
        prompt = f"""You are a data analyst assistant. A pandas DataFrame called `df` is already loaded.

{schema_context}

User's question: "{question}"

Your previous attempt failed. Previous code:
{previous_code}

Error received: {previous_error}

Fix the code. Write ONLY a corrected short Python code snippet (using pandas, dataframe is `df`)
that computes the answer and stores it in a variable called `result`. Only the code block,
no explanations. Keep it to 1-5 lines."""
    else:
        prompt = f"""You are a data analyst assistant. A pandas DataFrame called `df` is already loaded.

{schema_context}

User's question: "{question}"

Write ONLY a short Python code snippet (using pandas, the dataframe is `df`) that computes
the answer and stores it in a variable called `result`. Do not include explanations,
only the code block. Keep it to 1-5 lines."""

    response = model.generate_content(prompt)
    code = extract_code(response.text)

    safe_globals = {"pd": pd, "df": df}
    safe_locals = {}

    try:
        exec(code, safe_globals, safe_locals)
        result = safe_locals.get("result", "Result variable nahi mila.")
        return True, result, code
    except Exception as e:
        return False, str(e), code


def ask_question(df: pd.DataFrame, question: str, max_retries: int = 2) -> str:
    schema_context = build_schema_context(df)

    success, result, code = generate_and_run_code(df, question, schema_context)

    attempt = 1
    while not success and attempt <= max_retries:
        success, result, code = generate_and_run_code(
            df, question, schema_context, previous_error=result, previous_code=code
        )
        attempt += 1

    if not success:
        return "Sorry, is sawaal ka jawab nahi nikal paya. Thoda alag tarike se pooch ke dekho."

    if isinstance(result, (int, float, str)):
        return f"{question} ka jawab hai: {result}"

    explain_prompt = f"""The user asked: "{question}"
The computed answer is: {result}

Give a SHORT, spoken-style 1-2 sentence natural language answer (since this will be read aloud).
Match the user's language style (Hindi/English/Hinglish)."""

    explanation = model.generate_content(explain_prompt)
    return explanation.text


def main():
    print("=" * 55)
    print("JARVIS Voice Data Analyst")
    print("=" * 55)

    file_path = input("CSV/Excel file ka path do (type karke): ").strip().strip('"')

    try:
        df = load_file(file_path)
    except Exception as e:
        print(f"File load karne mein error: {e}")
        return

    speak(f"File loaded. {df.shape[0]} rows found. Ab aap bol ke sawaal pooch sakte hain.")

    while True:
        question = listen()

        if not question:
            continue

        if question.lower() in ["quit", "exit", "bye", "stop"]:
            speak("Goodbye!")
            break

        try:
            answer = ask_question(df, question)
            speak(answer)
        except Exception as e:
            print(f"Error: {e}")
            speak("Sorry, kuch error aa gaya.")


if __name__ == "__main__":
    main()
