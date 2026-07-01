import sys
from pathlib import Path
import os
import json
import requests
import yaml
from dotenv import load_dotenv
import re

def remove_emojis(text: str):
    if not isinstance(text, str):
        return ""
    emoji_pattern = re.compile(
        "[" 
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\u2600-\u26FF"
        "\u2700-\u27BF"
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub("", text)

# Path config
ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from funcs.memory.history_manager import manage_history

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def load_character_config():
    char_path = Path("character.yaml")
    if not char_path.exists():
        raise FileNotFoundError("Missing character.yaml file")
    with open(char_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return (
        data.get("model"),
        data.get("presets", {}).get("default", {}).get("system_prompt"),
        data.get("provider", {}),
        data.get("generation", {})
    )

def load_last_transcription():
    path = Path("data/global_data/last_transcription.json")
    if not path.exists(): return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f).get("text", "").strip()

def load_history():
    path = Path("history.json")
    if not path.exists(): return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def load_summary():
    path = Path("data/global_data/history_summary.json")
    if not path.exists(): return ""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f).get("summary", "")
    except:
        return []

# -----------------------------
#  DEFINICJA NATYWNYCH NARZĘDZI DLA API
# -----------------------------
DEFINED_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "vision_describe",
            "description": "Takes a screenshot of the user's main screen and analyzes what is on it.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    # {
    #     "type": "function",
    #     "function": {
    #         "name": "save_note",
    #         "description": "Nadpisuje lub tworzy nową notatkę z podaną treścią.",
    #         "parameters": {
    #             "type": "object",
    #             "properties": {
    #                 "content": {"type": "string", "description": "Treść notatki do zapisania"}
    #             },
    #             "required": ["content"]
    #         }
    #     }
    # },
    # {
    #     "type": "function",
    #     "function": {
    #         "name": "read_note",
    #         "description": "Odczytuje aktualną zawartość zapisanej notatki.",
    #         "parameters": {"type": "object", "properties": {}}
    #     }
    # },
    # {
    #     "type": "function",
    #     "function": {
    #         "name": "append_note",
    #         "description": "Dopisuje nową treść na końcu istniejącej notatki.",
    #         "parameters": {
    #             "type": "object",
    #             "properties": {
    #                 "content": {"type": "string", "description": "Tekst, który ma zostać dopisany"}
    #             },
    #             "required": ["content"]
    #         }
    #     }
    # },
    # {
    #     "type": "function",
    #     "function": {
    #         "name": "delete_note",
    #         "description": "Usuwa zapisaną notatkę.",
    #         "parameters": {"type": "object", "properties": {}}
    #     }
    # },
        {
        "type": "function",
        "function": {
            "name": "change_outfit",
            "description": "Changes Riko's outfit. Available: 'Riko1' (default), 'Riko_Thief' (thief), 'Corporate_Riko' (adult, office). Use when the user asks for a change of appearance, costume.",
            "parameters": {
                "type": "object",
                "properties": {
                    "skin_name": {"type": "string", "description": "Skin name: 'Riko1' or 'Riko_Thief' or 'Corporate_Riko'"}
                },
                "required": ["skin_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Searches the internet for current information and returns a summary.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search engine query"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "play_dance",
            "description": "Triggers a dance animation for Riko. Available dances: domo_jestem_geniuszem, Bling_Bang_Bang_Born, Dni_w_kolorze_jelenia, nie_jestem_diablem, shikanoko, Zlap_mnie_na_polu_pszenicy. The character will dance and return to idle afterwards. During the dance, other commands will be ignored.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dance_name": {
                        "type": "string",
                        "description": "Name of the dance to perform",
                        "enum": [
                            "domo_jestem_geniuszem",
                            "Bling_Bang_Bang_Born",
                            "Dni_w_kolorze_jelenia",
                            "nie_jestem_diablem",
                            "shikanoko",
                            "Zlap_mnie_na_polu_pszenicy"
                        ]
                    }
                },
                "required": ["dance_name"]
            }
        }
    }
]

def call_openrouter(model: str, messages: list, provider: dict, generation: dict, use_tools: bool = True):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": messages,
        **generation
    }
    if provider:
        payload["provider"] = provider
        
    if use_tools:
        payload["tools"] = DEFINED_TOOLS

    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code != 200:
        raise RuntimeError(f"API error: {resp.text}")

    data = resp.json()
    return data["choices"][0]["message"]


# -----------------------------
#  UNIWERSALNY ROUTER NARZĘDZI
# -----------------------------
def execute_tool(tool: str, args: dict):
    if tool == "vision_describe":
        try:
            from funcs.tools.vision.prtscr_vision_gemini import describe_image
            res = describe_image("ignored_path.png")
            return res.get("text") if isinstance(res, dict) else str(res)
        except Exception as e: return f"vision_describe error: {e}"

    # if tool == "save_note":
    #     try:
    #         from funcs.tools.files.save_note import save_note
    #         res = save_note(**args)
    #         return res.get("message") if isinstance(res, dict) else str(res)
    #     except Exception as e: return f"Błąd save_note: {e}"

    # elif tool == "read_note":
    #     try:
    #         from funcs.tools.files.read_note import read_note
    #         res = read_note()
    #         if isinstance(res, dict):
    #             return res.get("content") if res.get("status") == "success" else res.get("message")
    #         return str(res)
    #     except Exception as e: return f"Błąd read_note: {e}"

    # elif tool == "append_note":
    #     try:
    #         from funcs.tools.files.append_note import append_note
    #         res = append_note(**args)
    #         return res.get("message") if isinstance(res, dict) else str(res)
    #     except Exception as e: return f"Błąd append_note: {e}"

    # elif tool == "delete_note":
    #     try:
    #         from funcs.tools.files.delete_note import delete_note
    #         res = delete_note()
    #         return res.get("message") if isinstance(res, dict) else str(res)
    #     except Exception as e: return f"Błąd delete_note: {e}"

    if tool == "search_web":
        try:
            from funcs.tools.web.search_web import search_web
            res = search_web(**args)
            if isinstance(res, dict):
                return res.get("summary") if res.get("status") == "success" else res.get("message")
            return str(res)
        except Exception as e: return f"search_web error: {e}"

    if tool == "change_outfit":
        try:
            skin = args.get("skin_name", "Riko1")
            requests.post("http://localhost:8001/change_skin", json={"skin_name": skin}, timeout=5)
            return f"Outfit changed to: {skin}"
        except Exception as e:
            return f"Outfit change error: {e}"
        
    if tool == "play_dance":
        try:
            dance_map = {
                "domo_jestem_geniuszem": "/animations/vrma/domo_jestem_geniuszem.vrma",
                "Bling_Bang_Bang_Born": "/animations/vrma/Bling_Bang_Bang_Born.vrma",
                "Dni_w_kolorze_jelenia": "/animations/vrma/Dni_w_kolorze_jelenia.vrma",
                "nie_jestem_diablem": "/animations/vrma/nie_jestem_diablem.vrma",
                "shikanoko": "/animations/vrma/shikanoko.vrma",
                "Zlap_mnie_na_polu_pszenicy": "/animations/vrma/Zlap_mnie_na_polu_pszenicy.vrma",
            }
            dance_name = args.get("dance_name")
            if dance_name not in dance_map:
                return f"Unknown dance: {dance_name}"
            url = dance_map[dance_name]
            requests.post("http://localhost:8001/trigger_dance", json={"animation_url": url}, timeout=5)
            return f"Dance '{dance_name}' started."
        except Exception as e:
            return f"Dance launch error: {e}"

    return f"Unknown tool: {tool}"

# -----------------------------
#  MAIN LLM FUNCTION
# -----------------------------
def run_llm():
    try:
        model, system_prompt, provider, generation = load_character_config()
    except Exception as e:
        print(f"❌ Config problem: {e}")
        return

    user_text = load_last_transcription()
    if not user_text:
        return

    # --- Long-term memory (FAISS) ---

    from funcs.memory.vector_memory import VectorMemory
    from datetime import datetime
    memory = VectorMemory()
    memory_context = memory.get_context_block(user_text, top_k=5)
    current_time = datetime.now().strftime("%A, %d %B %Y,  %H:%M")


    # Check if there is a pending image (separate file).
    image_path = None
    try:
        pending = Path("data/global_data/pending_image.json")
        if pending.exists():
            with open(pending, "r", encoding="utf-8") as f:
                data = json.load(f)
                image_path = data.get("image_path")
            pending.unlink()
    except:
        pass

    # If there is an image, analyze it and add a description to the prompt.
    if image_path and Path(image_path).exists():
        print(f"🖼️ Analyzing image: {image_path}")
        try:
            from funcs.tools.vision.analyze_image import analyze_image
            image_description = analyze_image(image_path)
            user_text = f"{user_text}\n\n[Image uploaded by user. Description: {image_description}]"
            print(f"📝 Image description: {image_description[:100]}...")
        except Exception as e:
            print(f"⚠️ Image analysis error: {e}")

    history = load_history()
    summary = load_summary()


    messages = [{"role": "system", "content": system_prompt}]

    if summary:
        messages.append({"role": "system", "content": f"Relationship memory: {summary}"})

    # --- Long-term memory (FAISS + time) ---
    if memory_context:
        messages.append({"role": "system", "content": f"Current time: {current_time}\n\nLong-term memory:\n{memory_context}"})
    else:
        messages.append({"role": "system", "content": f"Current time: {current_time}"})

    for msg in history[-10:]:
        role = "user" if msg.get("role") == "user" else "assistant"
        messages.append({"role": role, "content": msg.get("text", "")})

    messages.append({"role": "user", "content": user_text})

    print("\n=== CONTEXT SENT TO OPENROUTER ===")
    for m in messages:
        print(m)

    final_answer = ""

    while True:
        try:
            response_message = call_openrouter(model, messages, provider, generation, use_tools=True)
        except Exception as e:
            print(f"❌ Błąd LLM: {e}")
            return

        messages.append(response_message)
        tool_calls = response_message.get("tool_calls")
        
        if not tool_calls:
            final_answer = response_message.get("content") or ""
            print(f"\n🤖 Odpowiedź Rico: {final_answer}")
            break

        for tool_call in tool_calls:
            tool_name = tool_call["function"]["name"]
            raw_args = tool_call["function"].get("arguments", "")

            # --- SAFE ARGUMENT PARSING ---
            if not raw_args or raw_args.strip() == "":
                tool_args = {}
            else:
                try:
                    tool_args = json.loads(raw_args)
                except Exception as e:
                    print(f"⚠️ Error parsing arguments: {raw_args} -> {e}")
                    tool_args = {}

            tool_call_id = tool_call["id"]

            print(f"\n🛠️ The model invoked a native tool.: {tool_name} with arguments: {tool_args}")

            tool_output = execute_tool(tool_name, tool_args)

            print(f"📸 Wynik dla {tool_name}: {tool_output}")

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call_id,
                "name": tool_name,
                "content": tool_output
            })


    # -----------------------------
    # Saving history and result files
    # -----------------------------
    clean_answer = remove_emojis(final_answer)
    manage_history(user_text, clean_answer)

    save_dir = Path("data/global_data")
    save_dir.mkdir(parents=True, exist_ok=True)
    with open(save_dir / "llm_answer.json", "w", encoding="utf-8") as f:
        json.dump({"text": clean_answer}, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    run_llm()
