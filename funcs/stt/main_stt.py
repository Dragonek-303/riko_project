# funcs/stt/main_stt.py
import sys
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = THIS_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config

from funcs.stt.stt_record import record_on_speech
from funcs.stt.stt_groq import transcribe_audio_groq

import json
import soundfile as sf
import requests

MANUAL_FLAG_PATH = config.DATA_GLOBAL / "manual_flag.json"
LAST_TRANS_PATH = config.DATA_GLOBAL / "last_transcription.json"
AUDIO_DIR = config.AUDIO_DIR

def check_manual_flag():
    if not MANUAL_FLAG_PATH.exists():
        return False
    try:
        return json.load(open(MANUAL_FLAG_PATH, "r", encoding="utf-8")).get("manual", False)
    except Exception:
        return False

def run_stt():

    if check_manual_flag():
        print("ℹ️ Manual flag already set - I skip STT.")
        return

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    audio_path = AUDIO_DIR / "conversation.wav"
    audio_path = str(audio_path)

    recorded = record_on_speech(
        output_file=audio_path,
        samplerate=44100,
        channels=1,
        silence_threshold=0.02,
        silence_duration=1.2
    )

    if recorded is None:
        print("ℹ️ Recording cancelled (manual input).")
        return

    try:
        with sf.SoundFile(audio_path) as f:
            duration = len(f) / f.samplerate
    except Exception as e:
        print(f"❌ Audio file read error: {e}")
        return

    print(f"🎧 Recording length: {duration:.2f} sek")

    if duration < 0.4:
        print("❌ The recording is too short — say something longer.")
        return

    try:
        text = transcribe_audio_groq(audio_path)
    except Exception as e:
        print(f"❌ Transcription error: {e}")
        return

    print("\n📝 Transcription:")
    print(text)

    try:
        LAST_TRANS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LAST_TRANS_PATH, "w", encoding="utf-8") as f:
            json.dump({"text": text}, f, ensure_ascii=False, indent=2)
        print(f"💾 Transcript saved to: {LAST_TRANS_PATH}")
    except Exception as e:
        print(f"[main_stt] Transcription save error: {e}")


if __name__ == "__main__":
    run_stt()
