# funcs/tools/vision/prtscr_vision_gemini.py
from pathlib import Path
import time
import mss
from PIL import Image
from google import genai
from dotenv import load_dotenv
import os

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# Gemini models ranked from best to worst
MODELS = [
    "gemini-3.5-flash",
    "gemini-3-flash-preview",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
]

# Local fallback model – import only when needed
_local_model = None
_local_processor = None


def _load_local_model():
    global _local_model, _local_processor
    if _local_model is None:
        print("🔄 Loading the local LFM2.5-VL as a fallback...")
        from transformers import AutoModelForImageTextToText, AutoProcessor
        import torch

        model_id = "LiquidAI/LFM2.5-VL-1.6B"
        _local_model = AutoModelForImageTextToText.from_pretrained(
            model_id,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True,
        )
        _local_processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
        print("✅ Local fallback ready")
    return _local_model, _local_processor


def _describe_with_local(image_path: str) -> str:
    """It describes the image using the local LFM2.5-VL model."""
    import torch

    model, processor = _load_local_model()
    image = Image.open(image_path).convert("RGB")

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


def capture_screenshot(save_path: Path):
    save_path.parent.mkdir(parents=True, exist_ok=True)
    with mss.mss() as sct:
        screenshot = sct.grab(sct.monitors[1])
        img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
        img.save(save_path)
    return save_path


def describe_image(image_path):
    """It takes a screenshot and describes it—first using Gemini, then a local fallback."""
    screenshot_path = Path("data/images/prtscreen_latest.png")
    capture_screenshot(screenshot_path)

    # 1. Spróbuj Gemini
    if client:
        with open(screenshot_path, "rb") as f:
            image_bytes = f.read()

        for model_name in MODELS:
            try:
                print(f"🖼️ Trying a model: {model_name}...")
                response = client.models.generate_content(
                    model=model_name,
                    contents=[
                        {"inline_data": {"mime_type": "image/png", "data": image_bytes}},
                        "Briefly and concisely describe what you see in this image. Do not use markdown..",
                    ],
                )
                text = response.text.strip()
                if text:
                    print(f"✅ The model worked out.: {model_name}")
                    return {"text": text}

            except Exception as e:
                error_msg = str(e)
                print(f"❌ {model_name} let down: {error_msg[:80]}...")
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    time.sleep(2)
                continue

    # 2. Fallback – local model
    try:
        print("🔄 All Gemini models failed – I’m switching to the local LFM2.5-VL...")
        text = _describe_with_local(str(screenshot_path))
        print("✅ The local model worked")
        return {"text": text}
    except Exception as e:
        return {"text": f"All models failed. Error: {e}"}


if __name__ == "__main__":
    result = describe_image("ignored_path.png")
    print(result)