#funcs\translate\translate_answer_google.py
import json
from pathlib import Path
from deep_translator import GoogleTranslator

# ROOT = project root directory
ROOT = Path(__file__).resolve().parents[2]

INPUT_PATH = ROOT / "data" / "global_data" / "llm_answer.json"
OUTPUT_PATH = ROOT / "data" / "global_data" / "translate_answer.json"

def translate_answer():
    if not INPUT_PATH.exists():
        print(f"❌ File not found: {INPUT_PATH}")
        return

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    text = data.get("text", "").strip()
    if not text:
        print("❌ No text to translate.")
        return

    translated = GoogleTranslator(source="pl", target="en").translate(text)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump({"text": translated}, f, ensure_ascii=False, indent=2)

    print(f"✅ Translated (Google) and saved to: {OUTPUT_PATH}")

if __name__ == "__main__":
    translate_answer()
