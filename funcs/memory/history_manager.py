# history_manager.py
import os
import json
from pathlib import Path
from datetime import datetime
from groq import Groq
from dotenv import load_dotenv
import re

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SUMMARY_MODEL = "qwen/qwen3.6-27b"
SUMMARY_INTERVAL = 10  # Interval for triggering conversation summarization

# ============================================================
# 1. HISTORY
# ============================================================

def load_history():
    path = Path("history.json")
    if not path.exists():
        return []
    try:
        return json.load(open(path, "r", encoding="utf-8"))
    except:
        print("⚠️ Failed to read history.json – creating a new history file.")
        return []

def save_history(history):
    # OPTIMIZATION: Keep only the last 20 messages in the file, 
    # as older interactions are already secured in the global summary and vector database.
    truncated_history = history[-20:]
    json.dump(truncated_history, open("history.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# ============================================================
# 2. SUMMARY
# ============================================================

def save_summary(summary_text):
    save_dir = Path("data/global_data")
    save_dir.mkdir(parents=True, exist_ok=True)
    json.dump({"summary": summary_text}, open(save_dir / "history_summary.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(f"💾 History summary saved to: data/global_data/history_summary.json")

def load_summary():
    path = Path("data/global_data/history_summary.json")
    if not path.exists():
        return ""
    try:
        return json.load(open(path, "r", encoding="utf-8")).get("summary", "")
    except:
        return ""

# ============================================================
# 3. MESSAGE COUNTER
# ============================================================

def load_summary_state():
    path = Path("data/global_data/summary_state.json")
    if not path.exists():
        return {"messages_since_summary": 0}
    try:
        return json.load(open(path, "r", encoding="utf-8"))
    except:
        return {"messages_since_summary": 0}

def save_summary_state(state):
    path = Path("data/global_data/summary_state.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    json.dump(state, open(path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

# ============================================================
# 4. GROQ SUMMARIZATION (FIXED)
# ============================================================

def summarize_history_groq(combined_history):
    if not GROQ_API_KEY:
        print("❌ Missing GROQ_API_KEY — unable to summarize conversation history.")
        return None

    client = Groq(api_key=GROQ_API_KEY)

    # REVISION: Iterating over the passed 'combined_history' slice instead of the global history
    full_text = ""
    for entry in combined_history:
        ts = entry.get("timestamp", "")
        role = entry.get("role", "")
        text = entry.get("text", "")
        if role == "system":
            full_text += f"[PREVIOUS SUMMARY]: {text}\n\n"
        else:
            full_text += f"[{ts}] {role}: {text}\n"

    print("📡 Sending filtered history slice to Groq for summarization...")

    try:
        response = client.chat.completions.create(
            model=SUMMARY_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Otrzymujesz listę fragmentów historii rozmowy. "
                        "Pierwszym fragmentem jest poprzednie streszczenie całej konwersacji. "
                        "Kolejne fragmenty to najnowsze wiadomości.\n"
                        "Twoim zadaniem jest stworzyć JEDNO zwięzłe streszczenie CAŁEJ rozmowy, "
                        "łącząc poprzednie streszczenie z nowymi wiadomościami.\n"
                        "Zasady:\n"
                        "- NIE dodawaj nowych informacji.\n"
                        "- NIE wymyślaj dialogów.\n"
                        "- NIE powtarzaj treści.\n"
                        "- NIE używaj tagów <think>.\n"
                        "- Zwróć TYLKO finalne streszczenie.\n"
                        "- Jeden, zwięzły akapit.\n"
                        "- Odpowiedź MUSI kończyć się pełnym zdaniem."
                    )
                },
                {
                    "role": "user",
                    "content": f"Streść tę rozmowę po polsku:\n\n{full_text}"
                }
            ],
            max_tokens=2000,
            # --- DISABLED REASONING EXTRA TOKENS ---
            reasoning_effort="none",   # Suppresses token generation for thinking phases
            reasoning_format="hidden", # Formats out the reasoning block from the output content
        )

        msg = response.choices[0].message
        content = getattr(msg, "content", "")

        content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()

        sentences = re.split(r'(?<=[.!?])\s*', content.strip())
        unique = []
        for s in sentences:
            clean = s.strip()
            if clean and clean not in unique:
                unique.append(clean)
        content = " ".join(unique).strip()

        if not content.endswith((".", "!", "?")):
            content += "."

        print("📨 Groq response:", content)
        return content

    except Exception as e:
        print(f"❌ Error during history summarization: {e}")
        return None

# ============================================================
# 5. MAIN HISTORY MANAGER FUNCTION
# ============================================================

def manage_history(new_user_text, new_assistant_text):
    history = load_history()
    now = datetime.now().isoformat(sep=" ", timespec="seconds")

    history.append({"role": "user", "text": new_user_text, "timestamp": now})
    history.append({"role": "assistant", "text": new_assistant_text, "timestamp": now})

    save_history(history)

    state = load_summary_state()
    state["messages_since_summary"] += 2

    if state["messages_since_summary"] >= SUMMARY_INTERVAL:
        print(f"⚠️ Reached {SUMMARY_INTERVAL} messages — triggering new summary generation...")

        previous_summary = load_summary()

        combined_history = []
        if previous_summary:
            combined_history.append({
                "role": "system",
                "text": previous_summary,
                "timestamp": now
            })
        
        # Pull only the defined conversational frame slice
        combined_history.extend(history[-SUMMARY_INTERVAL:])

        summary = summarize_history_groq(combined_history)

        if summary:
            save_summary(summary)
            state["messages_since_summary"] = 0  # reset counter

    save_summary_state(state)

# ============================================================
# 6. CONSOLIDATION INTO A VECTOR DATABASE
# ============================================================

import sys
from pathlib import Path as _Path
sys.path.append(str(_Path(__file__).resolve().parents[2]))  # root project

from funcs.memory.summarize import summarize_exchange
from funcs.memory.vector_memory import VectorMemory

CONSOLIDATION_INTERVAL = 3  # every 3 pairs (6 messages)

def consolidate_recent_pairs():
    """
    It checks whether three new pairs have been added since the last consolidation.
    If so, it consolidates them and saves them to FAISS..
    """
    state_path = _Path("data/global_data/consolidation_state.json")
    if state_path.exists():
        state = json.load(open(state_path, "r", encoding="utf-8"))
        last_consolidated_index = state.get("last_index", -1)
    else:
        last_consolidated_index = -1

    history = load_history()
    total_messages = len(history)

    # We are looking only for complete user-assistant pairs.
    new_pairs = []
    i = last_consolidated_index + 1
    while i < total_messages - 1:
        if history[i]["role"] == "user" and history[i+1]["role"] == "assistant":
            new_pairs.append((i, history[i]["text"], history[i+1]["text"]))
            i += 2
        else:
            i += 1
        if len(new_pairs) >= CONSOLIDATION_INTERVAL:
            break

    if len(new_pairs) < CONSOLIDATION_INTERVAL:
        return

    print(f"🧠 [MEMORY] Consolidating {len(new_pairs)} new pairs into FAISS...")
    memory = VectorMemory()

    for idx, user_text, assistant_text in new_pairs:
        fact = summarize_exchange(user_text, assistant_text)
        if fact:
            memory.add_fact(fact)
            print(f"💾 [FAISS SAVE] -> {fact}")

    memory.save()

    # Update status
    last_idx = new_pairs[-1][0] + 1  # index of the last assistant message
    state_path.parent.mkdir(parents=True, exist_ok=True)
    json.dump({"last_index": last_idx}, open(state_path, "w", encoding="utf-8"), indent=2)
