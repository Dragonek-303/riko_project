# funcs/stt/stt_record.py
import os
import sounddevice as sd
import numpy as np
import soundfile as sf
import queue
import sys
from pathlib import Path
import json

THIS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = THIS_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config

MANUAL_FLAG_PATH = config.DATA_GLOBAL / "manual_flag.json"

def _check_manual_flag():
    try:
        if not MANUAL_FLAG_PATH.exists():
            return False
        with open(MANUAL_FLAG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        val = bool(data.get("manual", False))
        print(f"[stt_record] _check_manual_flag -> {val}")
        return val
    except Exception as e:
        print(f"[stt_record] _check_manual_flag error: {e}")
        return False

def record_on_speech(output_file="conversation.wav", samplerate=44100, channels=1,
                     silence_threshold=0.02, silence_duration=1.0, device=None):
    if os.path.exists(output_file):
        try:
            os.remove(output_file)
        except Exception:
            pass

    q = queue.Queue()

    def callback(indata, frames, time_info, status):
        if status:
            print(status, file=sys.stderr)
        q.put(indata.copy())

    def rms_level(data):
        return np.sqrt(np.mean(np.square(data)))

    print(f"[stt_record] Starting InputStream, output_file={output_file}")
    try:
        with sf.SoundFile(output_file, mode='x', samplerate=samplerate,
                          channels=channels, subtype='PCM_16') as file:
            with sd.InputStream(samplerate=samplerate, device=device,
                                channels=channels, callback=callback):
                print("🎤 I'm waiting for you to start speaking...")
                silent_time = 0.0
                recording_started = False

                while True:
                    if _check_manual_flag():
                        print("✋ Manual input detected — I am stopping the recording.")
                        try:
                            file.close()
                            if os.path.exists(output_file):
                                os.remove(output_file)
                        except Exception as e:
                            print(f"[stt_record] cleanup error: {e}")
                        return None

                    try:
                        data = q.get(timeout=0.1)
                    except queue.Empty:
                        continue

                    rms = rms_level(data)

                    if not recording_started:
                        if rms > silence_threshold:
                            print("🔴 Recording...")
                            recording_started = True

                    if recording_started:
                        try:
                            file.write(data)
                        except Exception as e:
                            print(f"[stt_record] write error: {e}")

                        if rms < silence_threshold:
                            silent_time += len(data) / samplerate
                        else:
                            silent_time = 0.0

                        if silent_time >= silence_duration:
                            print("⏹️  Silence — recording stopped.")
                            break
    except Exception as e:
        print(f"[stt_record] InputStream error: {e}")
        try:
            if os.path.exists(output_file):
                os.remove(output_file)
        except Exception:
            pass
        return None

    return output_file
