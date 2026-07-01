"""It analyzes the uploaded image—first using Gemini (fallback), then the local LFM2.5-VL."""
from pathlib import Path
from PIL import Image
import torch
import time
from google import genai
from dotenv import load_dotenv
import os

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# Gemini models ranked from best to worst
MODELS = [
    "gemini-3.5-flash",
    "gemini-2.5-flash",
    "gemini-3-flash-preview",
    "gemini-2.5-flash-lite0",
]

# Local model – only when needed
_model = None
_processor = None


def _load_local_model():
    global _model, _processor
    if _model is None:
        print("🔄 I am loading the local LFM2.5-VL-1.6B...")
        from transformers import AutoModelForImageTextToText, AutoProcessor

        model_id = "LiquidAI/LFM2.5-VL-1.6B"
        _model = AutoModelForImageTextToText.from_pretrained(
            model_id,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True,
        )
        _processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
        print("✅ LFM2.5-VL ready")
    return _model, _processor


def _describe_with_gemini(image: Image, question: str) -> str | None:
    """I am trying to describe the image using Gemini. It returns `None` if all attempts fail."""
    if not _client:
        return None

    # Temporarily save to bytes
    import io
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    image_bytes = buf.getvalue()

    for model_name in MODELS:
        try:
            print(f"🖼️ I'm trying out Gemini.: {model_name}...")
            response = _client.models.generate_content(
                model=model_name,
                contents=[
                    {"inline_data": {"mime_type": "image/png", "data": image_bytes}},
                    question,
                ],
            )
            text = response.text.strip()
            if text:
                print(f"✅ It worked: {model_name}")
                return text
        except Exception as e:
            err = str(e)
            print(f"❌ {model_name}: {err[:80]}...")
            if "429" in err or "RESOURCE_EXHAUSTED" in err:
                time.sleep(2)
            continue
    return None


def _describe_with_local(image: Image, question: str) -> str:
    """It describes the image using the local LFM2.5-VL."""
    model, processor = _load_local_model()

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": "Briefly and concisely describe what you see in this image."},
            ],
        }
    ]

    prompt = processor.apply_chat_template(messages, add_generation_prompt=True)
    inputs = processor(text=prompt, images=image, return_tensors="pt")
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    with torch.no_grad():
        generated_ids = model.generate(**inputs, max_new_tokens=256, do_sample=False)

    result = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
    return result.split("\n")[-1].strip()


def analyze_image(image_path: str, question: str = None) -> str:
    """
    It analyzes the image—first using Gemini (with a fallback), then the local LFM2.5-VL.
    """
    try:
        image = Image.open(image_path).convert("RGB")

        if question is None:
            question = "Briefly and concisely describe what you see in this image, in Polish."

        # 1. Try Gemini
        gemini_result = _describe_with_gemini(image, question)
        if gemini_result:
            return gemini_result

        # 2. Fallback – local model
        print("🔄 Switching to the local LFM2.5-VL...")
        return _describe_with_local(image, question)

    except Exception as e:
        return f"Image analysis error: {e}"