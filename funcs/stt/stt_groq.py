import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


ASR_LANGUAGE = os.getenv("ASR_LANGUAGE", "pl")

def transcribe_audio_groq(audio_path="conversation.wav"):
    with open(audio_path, "rb") as f:
        result = client.audio.transcriptions.create(
            file=(audio_path, f.read()),
            model="whisper-large-v3",
            response_format="verbose_json",

            language=ASR_LANGUAGE,

            temperature=0,
            prompt=(
                f"Transcribe the audio EXACTLY as spoken, in {ASR_LANGUAGE}. "
                "Do NOT translate. Do NOT correct grammar. "
                "Do NOT guess English words. "
                "Keep slang, filler words, and mistakes exactly as they are."
            )
        )
        return result.text