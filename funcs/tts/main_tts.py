import uuid
import json
from pathlib import Path
import sys
import time
import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from funcs.tts.sovits_ping import sovits_gen, get_wav_duration
from funcs.tts.tts_preprocess import clean_llm_output
from funcs.vrm.vrm_client import set_vrm_state, vrm_talk


# ================================
#   MIXAMO ANIMATION HELPER
# ================================

def play_mixamo(animation_path):
    url = "http://localhost:8001/animate"
    payload = {
        "animate_type": "start_mixamo",
        "animation_url": animation_path,
        "play_once": False,
        "crop_start": 0.0,
        "crop_end": 0.0,
        "lock_position": False,
        "track_position": True,
    }
    try:
        requests.post(url, json=payload, timeout=2)
    except:
        print("⚠ Could not send Mixamo animation")


# ================================
#   CLEAN OLD AUDIO
# ================================

def clear_old_audio():
    root = Path(__file__).resolve().parents[2]
    audio_dir = root / "data" / "audio"

    for f in audio_dir.glob("tts_*.wav"):
        try:
            f.unlink()
            print(f"🗑 Deleted old audio: {f.name}")
        except Exception as e:
            print(f"⚠ Could not delete {f.name}: {e}")


# ================================
#   LOAD TRANSLATED TEXT (EN → TTS)
# ================================

def load_translated_text():
    root = Path(__file__).resolve().parents[2]
    path = root / "data" / "global_data" / "translate_answer.json"

    if not path.exists():
        print("❌ translate_answer.json not found")
        return None

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    text = data.get("text", "").strip()
    return text if text else None


# ================================
#   LOAD ORIGINAL TEXT (PL → SUBTITLES)
# ================================

def load_original_text():
    root = Path(__file__).resolve().parents[2]
    path = root / "data" / "global_data" / "llm_answer.json"

    if not path.exists():
        print("❌ llm_answer.json not found")
        return None

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    text = data.get("text", "").strip()
    return text if text else None


def ensure_dirs():
    root = Path(__file__).resolve().parents[2]
    (root / "data" / "audio").mkdir(parents=True, exist_ok=True)


def main_tts():
    ensure_dirs()

    # ENGLISH for TTS
    translated_text = load_translated_text()
    if not translated_text:
        print("❌ No translated text available")
        return

    # ORIGINAL for SUBTITLES
    original_text = load_original_text()
    if not original_text:
        print("❌ No original text available")
        return

    clean_translated = clean_llm_output(translated_text)
    clean_original = clean_llm_output(original_text)

    clear_old_audio()

    # Split into chunks (po kropkach)
    translated_chunks = [c.strip() for c in clean_translated.split(".") if c.strip()]

    if not translated_chunks:
        print("⚠ No chunks after splitting text.")
        play_mixamo("animations/mixamo/Idle.fbx")
        set_vrm_state("idle")
        return

    root = Path(__file__).resolve().parents[2]
    audio_dir = root / "data" / "audio"

    # THINKING ANIMATION
    play_mixamo("animations/mixamo/Thinking.fbx")
    set_vrm_state("thinking")
    time.sleep(1.2)

    # Generate all WAVs
    generated = []
    for chunk in translated_chunks:
        uid = uuid.uuid4().hex
        out_path = audio_dir / f"tts_{uid}.wav"

        print(f"🧠 Generating TTS for: {chunk!r}")
        sovits_gen(chunk, str(out_path))
        duration = get_wav_duration(out_path)

        generated.append((str(out_path), chunk, duration))
        print(f"🎧 Generated: {out_path.name} ({duration:.2f}s)")

    # TOTAL DURATION OF ALL CHUNKS
    total_duration = sum(d for _, _, d in generated)
    print(f"⏱ Total TTS duration: {total_duration:.2f}s")

    # TALKING ANIMATION
    set_vrm_state("talking")
    play_mixamo("animations/mixamo/Talking.fbx")

    time.sleep(0.2)

    # Send chunks
    for i, (audio_path, tts_chunk, duration) in enumerate(generated):

        if i == 0:
            # First chunk: full Polish text + total speaking time + 2 seconds
            subtitle_text = clean_original
            subtitle_duration = total_duration + 2.0
        else:
            # Next chunks: no subtitles, no timestamps.
            subtitle_text = ""
            subtitle_duration = 0.0

        print(f"📡 Sending to VRM: {audio_path} (subtitle on first chunk only)")
        vrm_talk(audio_path, "neutral", subtitle_text, int(subtitle_duration))
        time.sleep(duration + 0.1)

    time.sleep(0.2)

    # BACK TO IDLE
    play_mixamo("animations/mixamo/Idle.fbx")
    time.sleep(0.1)
    set_vrm_state("idle")

    print("✅ All chunks sent to VRM.")



if __name__ == "__main__":
    main_tts()