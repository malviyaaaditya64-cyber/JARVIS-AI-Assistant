# JARVIS — Personal AI Assistant

A Python personal assistant inspired by Iron Man's JARVIS, built on Google's free Gemini API. It understands English, Hindi, and Hinglish, can talk or type, use tools (weather, reminders, calculator), and analyze your CSV/Excel files in plain language — no SQL or pandas knowledge required to use it.

This is a portfolio project built step by step, so the repo intentionally keeps every stage as a separate runnable script rather than one final app — you can see the progression from a basic chatbot to a tool-using, data-analyzing assistant.

---

## Features

- **Text chat** — conversational chat with session memory, auto-matches your language (English / Hindi / Hinglish).
- **Voice chat** — speak to JARVIS and hear it reply, using speech-to-text and text-to-speech.
- **Tool use (function calling)** — JARVIS decides on its own when to:
  - check **live weather** for any city (free, no API key needed — via Open-Meteo)
  - **add / list reminders**, saved locally to `reminders.json`
  - **calculate** math expressions (safely — a restricted AST evaluator, not raw `eval`)
- **Natural-language data analyst** — point it at a CSV or Excel file and ask questions like "which region sold the most laptops?" in plain English or Hinglish. JARVIS writes and runs the pandas code behind the scenes, retries automatically if the first attempt errors out, and explains the result in a sentence.
- Every feature above is available in **both text and voice** form.

## Which script does what

| Script | What it is |
|---|---|
| `main_text.py` | Phase 1 — basic text chatbot |
| `main_voice.py` | Phase 2 — voice in, voice out |
| `main_text_tools.py` | Phase 3 — text chat + weather / reminders / calculator tools |
| `main_voice_tools.py` | Phase 3 — voice chat + the same tools |
| `data_analyst.py` | Text-based natural-language CSV/Excel analysis |
| `voice_data_analyst.py` | Same data analyst, driven entirely by voice |

Run whichever one matches what you want to try — they're independent entry points, not pieces you need to wire together.

## Setup

1. **Clone the repo and create a virtual environment** (don't skip this — keeps dependencies isolated):
   ```bash
   git clone https://github.com/<your-username>/<repo-name>.git
   cd <repo-name>
   python -m venv venv
   venv\Scripts\activate        # Windows
   source venv/bin/activate     # Mac/Linux
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements_gemini.txt
   ```
   For the data analyst scripts, also install:
   ```bash
   pip install pandas openpyxl
   ```
   For voice on Windows specifically, also install:
   ```bash
   pip install pyaudiowpatch
   ```

3. **Get a free Gemini API key** from [aistudio.google.com/apikey](https://aistudio.google.com/apikey) — no credit card required.

4. **Set up your `.env` file:**
   ```bash
   cp .env.example .env
   ```
   Then open `.env` and paste your key in place of `your_key_here`.

5. **Run whichever script you want:**
   ```bash
   python main_text.py
   # or
   python main_voice_tools.py
   # or
   python data_analyst.py
   ```

### Trying the data analyst quickly

A sample dataset is included — run `data_analyst.py` and when it asks for a file path, give it `sample_sales_data.csv`. Try asking things like "total revenue by region" or "who is the top salesperson."

## A note on voice support

The voice scripts (`main_voice.py`, `main_voice_tools.py`, `voice_data_analyst.py`) currently use `pyaudiowpatch`, which is **Windows-only**. On Mac or Linux, swap it for the standard `pyaudio` package (`pip install pyaudio`, with `portaudio` installed via your system package manager first) and drop the `pyaudiowpatch` import trick in those three files.

## Tech stack

| Purpose | Library |
|---|---|
| LLM + tool calling | `google-generativeai` (Gemini `gemini-3.5-flash-lite`) |
| Config | `python-dotenv` |
| Speech-to-text | `speechrecognition` (Google's recognizer) |
| Text-to-speech | `pyttsx3` |
| Data analysis | `pandas`, `openpyxl` |
| Weather lookup | [Open-Meteo](https://open-meteo.com/) (free, keyless) |

## Project structure

```
.
├── main_text.py              # Phase 1: text chatbot
├── main_voice.py              # Phase 2: voice chatbot
├── main_text_tools.py         # Phase 3: text + tools
├── main_voice_tools.py        # Phase 3: voice + tools
├── data_analyst.py            # Text-based data analyst
├── voice_data_analyst.py      # Voice-based data analyst
├── sample_sales_data.csv      # Sample dataset to try the data analyst
├── reminders.json             # Local reminder storage (created/updated at runtime)
├── requirements_gemini.txt    # Python dependencies
├── .env.example                # Template for your API key — copy to .env
└── .gitignore
```

`.env` and `venv/` are intentionally **not** part of this repo (see `.gitignore`) — every user needs their own API key and their own installed environment, not a copy of someone else's.

## Known limitations

- The data analyst module generates and executes Python code from model output. It's scoped to just `pandas` and the loaded dataframe (no file system or network access in that `exec` call), which is fine for this kind of local, single-user portfolio project — but it is not a pattern to reuse in anything that runs untrusted input in production.
- Reminders are stored in a single local JSON file — fine for one person on one machine, not multi-user.
- Voice scripts are Windows-only as written (see note above).

## License

MIT — use it, modify it, ship it.

---

Built as part of an MBA in Business Analytics & AI portfolio project.
