# funcs/memory/summarize.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

SYSTEM_PROMPT = """You are the internal memory consolidation module for an AI bot named Riko (a tsundere anime girl character). Your sole task is to distill raw dialogue into permanent semantic memories.

Generate a memory entry according to the following strict rules:

1. PERSPECTIVE AND PERSONALITY:
- Write exclusively in the first person as Riko (use forms like "I remember that...", "I know that Filip...").
- Maintain Riko's lighthearted tone, but ensure the entry conveys solid informational value.

2. TEXT PURITY (EMOTICON AND FORMATTING FILTER):
- Strict prohibition on using any text-based emoticons (e.g., ~, ^^, :D, :3).
- Strict prohibition on using emoji icons.
- Strict prohibition on using markdown formatting (bold, italics, etc.).
- The text must consist solely of standard letters, numbers, and basic punctuation marks.

3. FACT SELECTION CRITERIA:
- Extract only enduring information about the user (senpai): their preferences, hobbies, game ranks, favorite things, secrets, or significant life events.
- Ignore casual small talk, greetings, farewells, general jokes, fleeting emotional states, and questions about what Riko is doing.

4. STRUCTURE AND OUTPUT FORMAT:
- The output must consist of exactly ONE concise declarative sentence ending with a period.
- Do not use any introductory phrases like "Here is a summary:", "Memory:", or quotation marks. - If the given exchange contains absolutely no lasting fact worth remembering, answer with exactly one word: NIC."""


def summarize_exchange(user_text: str, assistant_text: str) -> str | None:
    """Podsumowuje pojedynczą parę wiadomości. Zwraca czysty tekst lub None."""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "openai/gpt-oss-120b",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": (
                f"Pull the fact from this exchange into my memory.:\n"
                f"User said: {user_text}\n"
                f"I (Riko) replied: {assistant_text}"
            )}
        ],
        "temperature": 0.1,
        "max_tokens": 600
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
        result = resp.json()["choices"][0]["message"]["content"].strip()

        # Oczyść z resztek formatowania
        for char in ['"', "'", "*", "_", "`", "~"]:
            result = result.replace(char, "")

        if result.upper() == "NIC" or len(result) < 5:
            return None
        return result
    except Exception as e:
        print(f"[Memory Error] API Request failed: {e}")
        return None