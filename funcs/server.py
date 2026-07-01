# funcs/server.py
import asyncio
import json
import logging
from typing import Optional, Set
from pathlib import Path
import os
import time
from funcs.click_reactions import build_click_reaction

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi import UploadFile, File

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# === STATIC AUDIO DIRECTORY ===
AUDIO_DIR = Path(__file__).resolve().parent.parent / "data" / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
print("AUDIO_DIR =", AUDIO_DIR)

app.mount("/audio", StaticFiles(directory=str(AUDIO_DIR)), name="audio")

ANIM_DIR = Path(__file__).resolve().parent.parent / "client" / "animations"
app.mount("/animations", StaticFiles(directory=str(ANIM_DIR)), name="animations")

MODELS_DIR = Path(__file__).resolve().parent.parent / "client" / "models"
app.mount("/models", StaticFiles(directory=str(MODELS_DIR)), name="models")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================================
# MODELS
# ================================

class AnimationPayload(BaseModel):
    animate_type: str
    animation_url: str
    play_once: Optional[bool] = False
    crop_start: Optional[float] = 0.0
    crop_end: Optional[float] = 0.0
    lock_position: Optional[bool] = False
    track_position: Optional[bool] = True


class CombinedPayload(BaseModel):
    animation_url: str
    audio_path: str
    expression: str = "neutral"
    delay: float = 0.0


class SetStateRequest(BaseModel):
    state: str


class TalkRequest(BaseModel):
    audio_path: str
    expression: str = "neutral"
    audio_text: str
    audio_duraction: int


# ================================
# WEBSOCKETS
# ================================

active_connections: Set[WebSocket] = set()
status_connections: Set[WebSocket] = set()

html = """
<!DOCTYPE html>
<html>
  <head><title>VRM Trigger Server</title></head>
  <body>
    <h1>VRM Trigger Server</h1>
    <p>WebSocket clients: <span id="count">0</span></p>
    <script>
      const ws = new WebSocket(`ws://${location.host}/ws_status`);
      ws.onmessage = e => {
        const msg = JSON.parse(e.data);
        if (msg.type === 'count_update') {
          document.getElementById('count').textContent = msg.count;
        }
      };
    </script>
  </body>
</html>
"""

@app.get("/")
async def root():
    return HTMLResponse(html)


async def notify_clients(message: dict):
    if not active_connections:
        logger.info("No clients connected; skipping notify.")
        return
    data = json.dumps(message)
    logger.info(f"Broadcasting to {len(active_connections)} client(s): {data}")
    coros = [ws.send_text(data) for ws in list(active_connections)]
    results = await asyncio.gather(*coros, return_exceptions=True)
    for ws, res in zip(list(active_connections), results):
        if isinstance(res, Exception):
            logger.error(f"Failed to send to {ws.client}: {res}")
            active_connections.discard(ws)


async def broadcast_status(count: int):
    msg = json.dumps({"type": "count_update", "count": count})
    coros = [ws.send_text(msg) for ws in list(status_connections)]
    await asyncio.gather(*coros, return_exceptions=True)


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    active_connections.add(ws)
    logger.info(f"Client connected: {ws.client} (total {len(active_connections)})")
    await broadcast_status(len(active_connections))
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        active_connections.discard(ws)
        logger.info(f"Client disconnected: {ws.client} (total {len(active_connections)})")
        await broadcast_status(len(active_connections))
    except Exception as e:
        logger.error(f"WS error: {e}")
        active_connections.discard(ws)
        await broadcast_status(len(active_connections))


@app.websocket("/ws_status")
async def ws_status(ws: WebSocket):
    await ws.accept()
    status_connections.add(ws)
    await ws.send_text(json.dumps({"type": "count_update", "count": len(active_connections)}))
    try:
        while True:
            msg = await ws.receive_text()
            if msg == "ping":
                await ws.send_text("pong")
    except WebSocketDisconnect:
        status_connections.discard(ws)
    except Exception:
        status_connections.discard(ws)


# ================================
# HTTP Endpoints
# ================================

@app.post("/talk")
async def talk(req: TalkRequest):
    payload = {
        "type": "start_animation",
        "audio_path": req.audio_path,
        "expression": req.expression,
        "audio_text": req.audio_text,
        "audio_duraction": req.audio_duraction
    }
    await notify_clients(payload)
    return {"status": "sent", "payload": payload}


@app.post("/animate")
async def animate(payload: AnimationPayload):
    anim_type = payload.animate_type
    if anim_type == "auto":
        url_lower = payload.animation_url.lower()
        if url_lower.endswith(".vrma"):
            anim_type = "start_vrma"
        elif url_lower.endswith(".fbx"):
            anim_type = "start_mixamo"
        else:
            anim_type = "start_mixamo"
        logger.info(f"Auto-detected animation type: {anim_type} for {payload.animation_url}")

    forwarded = {
        "type": anim_type,
        "animation_url": payload.animation_url,
        "play_once": payload.play_once,
        "crop_start": payload.crop_start,
        "crop_end": payload.crop_end,
        "lock_position": payload.lock_position,
        "track_position": payload.track_position,
    }

    await notify_clients(forwarded)
    return {"status": "sent", "payload": forwarded}


@app.post("/set_state")
async def set_state(req: SetStateRequest):
    valid_states = ["idle", "listening", "thinking", "talking"]
    if req.state not in valid_states:
        return {
            "status": "error",
            "message": f"Invalid state: {req.state}",
            "valid_states": valid_states
        }

    payload = {
        "type": "set_state",
        "state": req.state
    }
    await notify_clients(payload)
    return {
        "status": "state_set",
        "state": req.state
    }


# ================================
# /manual_text
# ================================

@app.post("/manual_text")
async def manual_text(payload: dict):
    text = payload.get("text", "").strip()
    manual = payload.get("manual", False)

    save_dir = Path(__file__).resolve().parent.parent / "data" / "global_data"
    save_dir.mkdir(parents=True, exist_ok=True)

    with open(save_dir / "last_transcription.json", "w", encoding="utf-8") as f:
        json.dump({"text": text}, f, ensure_ascii=False, indent=2)

    with open(save_dir / "manual_flag.json", "w", encoding="utf-8") as f:
        json.dump({"manual": manual}, f)

    return {"status": "ok"}


# ================================
# CLICK INTERACTION
# ================================

class ClickInteractionRequest(BaseModel):
    type: str
    bone: str
    region: str

async def _broadcast_idle_after(payload: dict, delay: float):
    await asyncio.sleep(delay)
    await notify_clients(payload)

@app.post("/send_click_interaction")
async def send_click_interaction(req: ClickInteractionRequest):
    reaction = build_click_reaction(req.region, req.bone)

    await notify_clients(reaction["sound"])
    await notify_clients(reaction["animation"])

    _pending_user_actions.append({
        "region": req.region,
        "bone": req.bone,
        "ts": time.time()
    })

    return {
        "status": "click_handled",
        "region": req.region,
        "bone": req.bone,
    }



# ================================
# PENDING ACTIONS (for main.py)
# ================================

_pending_user_actions: list = []

@app.get("/pop_pending_actions")
async def pop_pending_actions():
    global _pending_user_actions
    actions = _pending_user_actions
    _pending_user_actions = []
    return {"actions": actions, "count": len(actions)}


# ================================
# IMAGE UPLOAD
# ================================

UPLOADS_DIR = Path(__file__).resolve().parent.parent / "data" / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

@app.post("/upload_image")
async def upload_image(file: UploadFile = File(...)):
    """It receives the image from the frontend, saves it, and saves the path to `pending_image.json`."""
    import uuid
    ext = file.filename.split(".")[-1] if "." in file.filename else "png"
    filename = f"upload_{uuid.uuid4().hex}.{ext}"
    filepath = UPLOADS_DIR / filename

    with open(filepath, "wb") as f:
        content = await file.read()
        f.write(content)

    image_path_str = str(filepath).replace("\\", "/")

    # Save the image path to pending_image.json (a separate file).
    save_dir = Path(__file__).resolve().parent.parent / "data" / "global_data"
    save_dir.mkdir(parents=True, exist_ok=True)

    with open(save_dir / "pending_image.json", "w", encoding="utf-8") as f:
        json.dump({"image_path": image_path_str}, f)

    logger.info(f"📷 Image saved: {image_path_str}")
    return {"status": "ok", "filename": filename, "path": image_path_str}


# ================================
# CHANGE SKIN
# ================================

class ChangeSkinRequest(BaseModel):
    skin_name: str

@app.post("/change_skin")
async def change_skin(req: ChangeSkinRequest):
    skin_path = f"./models/{req.skin_name}.vrm"
    payload = {"type": "change_skin", "skin_path": skin_path}
    await notify_clients(payload)
    logger.info(f"👗 Skin changed to: {skin_path}")
    return {"status": "ok", "skin": req.skin_name}


class DanceTrigger(BaseModel):
    animation_url: str
    play_once: bool = True
    lock_position: bool = True
    track_position: bool = False

@app.post("/trigger_dance")
async def trigger_dance(req: DanceTrigger):
    payload = {
        "type": "start_vrma",
        "animation_url": req.animation_url,
        "play_once": req.play_once,
        "lock_position": req.lock_position,
        "track_position": req.track_position,
    }
    await notify_clients(payload)
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("funcs.server:app", host="0.0.0.0", port=8001, reload=True)
