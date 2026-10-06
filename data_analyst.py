"""
JARVIS - Data Analyst Module (CSV/Excel Analysis via Natural Language)
--------------------------------------------------------------------------
Yeh module CSV/Excel file load karta hai aur aapko plain English/Hinglish mein
questions poochne deta hai. JARVIS internally Pandas code generate karke
answer nikalta hai.

Setup:
- pip install pandas openpyxl
- (google-generativeai aur python-dotenv already installed hone chahiye)

Run: python data_analyst.py
"""

import os
import re
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel(model_name="gemini-3.5-flash-lite")


def load_file(path: str) -> pd.DataFrame:
    """CSV ya Excel file ko load karta hai, extension ke hisaab se.
    Real-world files mein encoding issues ya multiple sheets ho sakte hain, unhe handle karta hai."""
    if path.endswith(".csv"):
        try:
            return pd.read_csv(path)
        except UnicodeDecodeError:
            # Kuch CSV files UTF-8 mein nahi hoti (jaise Excel se export ki hui) - fallback try karo
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
    """DataFrame ka structure (columns, types, sample rows) text mein describe karta hai
    taaki Gemini ko pata chale data kaisa hai, bina poora data bheje"""
    schema = f"Columns and types:\n{df.dtypes.to_string()}\n\n"
    schema += f"Shape: {df.shape[0]} rows, {df.shape[1]} columns\n\n"
    schema += f"First 3 rows (sample):\n{df.head(3).to_string()}\n"
    return schema


def extract_code(response_text: str) -> str:
    """Gemini ke response se sirf Python code nikalta hai (markdown fences hata ke)"""
    match = re.search(r"```(?:python)?\s*(.*?)```", response_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return response_text.strip()


def generate_and_run_code(df: pd.DataFrame, question: str, schema_context: str, previous_error: str = None, previous_code: str = None) -> tuple:
    """Ek attempt mein code generate karke run karta hai. Returns (success, result_or_error, code)"""

    if previous_error:
        # Retry: pichli baar ki error dikha ke fix karne ko kehte hain
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

    # SAFETY NOTE: Yeh sirf ek restricted local project ke liye hai (portfolio demo).
    # Production mein aisa raw code execution NEVER karna chahiye untrusted input pe.
    safe_globals = {"pd": pd, "df": df}
    safe_locals = {}

    try:
        exec(code, safe_globals, safe_locals)
        result = safe_locals.get("result", "Result variable nahi mila code mein.")
        return True, result, code
    except Exception as e:
        return False, str(e), code


def ask_question(df: pd.DataFrame, question: str, max_retries: int = 2) -> str:
    """User ka natural language question leke Pandas code generate karta hai,
    use safely run karta hai (fail hone par khud-correct karta hai), aur result return karta hai"""

    schema_context = build_schema_context(df)

    success, result, code = generate_and_run_code(df, question, schema_context)

    # Agar fail hua, to error ke saath retry karo (max_retries baar)
    attempt = 1
    while not success and attempt <= max_retries:
        success, result, code = generate_and_run_code(
            df, question, schema_context, previous_error=result, previous_code=code
        )
        attempt += 1

    if not success:
        return f"Maine {attempt} baar try kiya lekin answer nahi nikal paya. Error: {result}\nShayad question ko thoda alag tarike se pooch ke dekho."

    # Simple results (numbers/strings) ko seedha format kar dete hain - extra API call nahi lagti
    if isinstance(result, (int, float, str)):
        return f"{question} -> {result}"

    # Complex results (DataFrame/Series) ke liye hi explanation call karte hain
    explain_prompt = f"""The user asked: "{question}"
The computed answer is: {result}

Give a short, clear 1-2 sentence natural language answer based on this result.
Match the user's language style (Hindi/English/Hinglish)."""

    explanation = model.generate_content(explain_prompt)
    return explanation.text


def main():
    print("=" * 55)
    print("JARVIS Data Analyst")
    print("=" * 55)

    file_path = input("CSV/Excel file ka path do: ").strip().strip('"')

    try:
        df = load_file(file_path)
    except Exception as e:
        print(f"File load karne mein error: {e}")
        return

    print(f"\nFile loaded! {df.shape[0]} rows, {df.shape[1]} columns.")
    print(f"Columns: {list(df.columns)}\n")
    print("Ab aap data ke baare mein questions pooch sakte ho. 'quit' type karo exit ke liye.\n")

    while True:
        question = input("You: ").strip()

        if question.lower() in ["quit", "exit", "bye"]:
            print("JARVIS: Goodbye!")
            break

        if not question:
            continue

        try:
            answer = ask_question(df, question)
            print(f"\nJARVIS: {answer}\n")
        except Exception as e:
            print(f"Error: {e}\n")


if __name__ == "__main__":
    main()
