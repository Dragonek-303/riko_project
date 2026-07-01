from pathlib import Path
import requests

BASE_URL = "http://127.0.0.1:8001"



# ================================
#   SET STATE
# ================================

def set_vrm_state(state: str):
    """
    Ustawia stan avatara:
    idle, listening, thinking, talking
    """
    url = f"{BASE_URL}/set_state"
    payload = {"state": state}

    try:
        resp = requests.post(url, json=payload)
        print(f"[VRM] set_state({state}) → {resp.status_code}")
    except Exception as e:
        print(f"[VRM] set_state error: {e}")


# ================================
#   TALK
# ================================

def vrm_talk(audio_path: str, expression: str, audio_text: str, audio_duration: float):
    """
    Sends information about the audio chunk to the VRM..

    audio_path – local path to the .wav file
    VRM receives the URL: http://localhost:8001/audio/<file.wav>
    """
    url = f"{BASE_URL}/talk"

    audio_file_name = Path(audio_path).name
    audio_url = f"{BASE_URL}/audio/{audio_file_name}"

    payload = {
        "audio_path": audio_url,
        "expression": expression,
        "audio_text": audio_text,
        "audio_duraction": int(audio_duration),
    }

    try:
        resp = requests.post(url, json=payload)
        print(f"[VRM] talk → {resp.status_code}")
    except Exception as e:
        print(f"[VRM] talk error: {e}")


# ================================
#   ANIMACJE
# ================================

def vrm_animate(animation_type: str, animation_url: str,
                play_once=False, crop_start=0.0, crop_end=0.0,
                lock_position=False, track_position=True):
    """
    Triggers a VRMA or Mixamo animation..
    """
    url = f"{BASE_URL}/animate"

    payload = {
        "animate_type": animation_type,
        "animation_url": animation_url,
        "play_once": play_once,
        "crop_start": crop_start,
        "crop_end": crop_end,
        "lock_position": lock_position,
        "track_position": track_position,
    }

    try:
        resp = requests.post(url, json=payload)
        print(f"[VRM] animate → {resp.status_code}")
    except Exception as e:
        print(f"[VRM] animate error: {e}")
