# main.py
import time
import traceback
import json
import sys
from pathlib import Path
from threading import Thread

import requests

# Ensure project root is on sys.path so imports work regardless of CWD
THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

import config

from funcs.stt.main_stt import run_stt
from funcs.llm.main_llm import run_llm
from funcs.translate.translate_answer_google import translate_answer
from funcs.tts.main_tts import main_tts

MANUAL_FLAG = config.DATA_GLOBAL / "manual_flag.json"
LAST_TRANS = config.DATA_GLOBAL / "last_transcription.json"

SERVER_BASE_URL = "http://localhost:8001"

# ==================== CLICK ====================

def _action_to_text(action: dict) -> str:
    region = (action.get("region") or "").strip()
    bone = (action.get("bone") or "").strip()
    if region and region.lower() != "body":
        label = region.replace("_", " ")
    elif bone:
        label = bone.replace("_", " ")
    else:
        label = "body"
    return f"[the user touched your {label}]"


def fetch_pending_user_actions() -> list:
    try:
        resp = requests.get(f"{SERVER_BASE_URL}/pop_pending_actions", timeout=2)
        resp.raise_for_status()
        return resp.json().get("actions", [])
    except Exception as e:
        print(f"[click] fetch_pending_user_actions failed: {e}")
        return []


# Flag: whether the click is ready to be processed
_click_ready = False
_click_text = ""


def click_dispatcher(poll_interval: float = 0.5):
    print(f"[click] dispatcher started (poll every {poll_interval}s)")
    while True:
        try:
            actions = fetch_pending_user_actions()
            if actions:
                user_text = " ".join(_action_to_text(a) for a in actions)
                print(f"[click] {len(actions)} action(s): {user_text}")

                # Save the click as a transcription.
                LAST_TRANS.parent.mkdir(parents=True, exist_ok=True)
                with open(LAST_TRANS, "w", encoding="utf-8") as f:
                    json.dump({"text": user_text}, f, ensure_ascii=False, indent=2)

                # Set manual_flag = True to interrupt STT.
                MANUAL_FLAG.parent.mkdir(parents=True, exist_ok=True)
                with open(MANUAL_FLAG, "w", encoding="utf-8") as f:
                    json.dump({"manual": True}, f)

                print(f"[click] saved + manual flag set")
        except Exception as e:
            print(f"[click] dispatcher error: {e}")
        time.sleep(poll_interval)


# ==================== RESZTA ====================

def pop_manual_flag():
    try:
        if not MANUAL_FLAG.exists():
            return False
        with open(MANUAL_FLAG, "r", encoding="utf-8") as f:
            data = json.load(f)
        try:
            MANUAL_FLAG.unlink()
        except Exception:
            pass
        return bool(data.get("manual", False))
    except Exception:
        try:
            if MANUAL_FLAG.exists():
                MANUAL_FLAG.unlink()
        except Exception:
            pass
        return False


def clear_manual_flag():
    try:
        if MANUAL_FLAG.exists():
            MANUAL_FLAG.unlink()
    except Exception:
        pass


def clear_last_trans():
    """Delete the last_transcription file so it isn't repeated."""
    try:
        if LAST_TRANS.exists():
            LAST_TRANS.unlink()
    except Exception:
        pass


def main():
    print("=====================================")
    print("        RIKO VOICE ASSISTANT")
    print("=====================================")

    Thread(target=click_dispatcher, args=(0.5,), daemon=True).start()

    while True:
        try:
            if pop_manual_flag():
                print("\n⌨️ Manual input / click detected — Skipping STT.")
            else:
                clear_last_trans()
                print("\n🎤 [STT] Waiting for a statement...")
                run_stt()

            print("\n🧠 [LLM] Generating a response...")
            run_llm()

            print("\n🌐 [TRANSLATE] Translating the answer...")
            translate_answer()

            print("\n🔊 [TTS] Generate audio and animations...")
            main_tts()

            # --- MEMORY CONSOLIDATION (every 3 pairs) ---
            try:
                from funcs.memory.history_manager import consolidate_recent_pairs
                consolidate_recent_pairs()
            except Exception as e:
                print(f"[Memory] Consolidation failed: {e}")

            clear_last_trans()
            clear_manual_flag()

            print("\n⏳ All set. You can continue speaking or writing...")
            time.sleep(0.5)

        except KeyboardInterrupt:
            print("\n🛑 Stopped manually.")
            break

        except Exception as e:
            print("\n❌ Loop error:")
            print(e)
            traceback.print_exc()
            time.sleep(1)


if __name__ == "__main__":
    main()