![Python](https://img.shields.io/badge/Python-3.10-blue?logo=python)
![Platform](https://img.shields.io/badge/Platform-Windows-blue?logo=windows)
![Frontend](https://img.shields.io/badge/Frontend-Vite-yellow?logo=vite)
![Backend](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi)
![3D](https://img.shields.io/badge/3D-VRM%20%2B%20Three.js-green)
![AI](https://img.shields.io/badge/AI-LLM%20Agent-purple)
![Voice](https://img.shields.io/badge/Voice-GPT--SoVITS-orange)
![Status](https://img.shields.io/badge/Status-Active-success)
![Complexity](https://img.shields.io/badge/Complexity-High%20(Research%20Project)-red)

---



# 🦊 Project Riko

> Interactive AI companion with 3D VRM avatar, voice synthesis, and LLM-driven personality system.


## ⚠️ What is this?

Project Riko is a **distributed AI companion system**, not a chatbot.

It combines:

- LLM reasoning (OpenRouter / Groq / Gemini)
- Voice synthesis (GPT-SoVITS)
- 3D VRM avatar (Three.js)
- Tool usage (search, vision, memory)
- Real-time interaction system

> ⚠️ Note: This is a multi-service AI system. First startup may take time depending on hardware and dependencies.

---

## 🧠 System Architecture

```text
User (text / voice)
        ↓
Frontend (Vite + VRM UI)
        ↓
Backend (FastAPI)
        ↓
LLM (OpenRouter / Groq / Gemini)
        ↓
Tools (search / vision / memory)
        ↓
Response (EN)
        ↓
GPT-SoVITS TTS
        ↓
Audio → frontend
        ↓
VRM avatar animation + lip sync
````

---


## 🚀 Quick Start

### 1. Clone repo

```bash
git clone https://github.com/Dragonek-303/riko_project.git
cd riko_project
```

---

### 2. Python environment

```bash
python -m venv .venv
.venv\Scripts\activate

pip install uv
```

### ❓ Why uv is used?

`uv` is used to speed up dependency installation and avoid resolver issues in heavy AI stacks.
👉 It is NOT required for the project to run.

Use `uv` only if you want faster setup.

---

### 3. Install PyTorch

Install PyTorch manually before dependencies to avoid wrong builds:

#### CPU version:

```bash
uv pip install torch==2.10.0
```

#### GPU version (CUDA 13):

```bash
uv pip install torch==2.10.0 --index-url https://download.pytorch.org/whl/cu130
```

---

### 4. Install Python dependencies

After installing PyTorch:

```bash
uv pip install -r requirements.txt
```

or without uv:

```bash
pip install -r requirements.txt
```

---

### 5. Install Frontend dependencies (IMPORTANT – first run only)

Before starting the project for the first time, install Node.js dependencies:

```bash
cd client
npm install
cd ..
```

👉 This step is required only once after cloning the repository.
`node_modules` is not included in the repo and is generated automatically.

---

### 6. Environment variables

Create `.env`:

```env
GROQ_API_KEY=your_key
OPENROUTER_API_KEY=your_key
GEMINI_API_KEY=your_key
SERPAPI_KEY=your_key
ASR_LANGUAGE=YOUR LANGUAGE for example:pl
```


---

## 🎭 Character Customization (character.yaml)

Project Riko is fully controlled by the `character.yaml` file — no code changes required.

---

### 🧠 Main Personality Control

All behavior, language, tone, and personality are defined here:

```yaml
presets:
  default:
    system_prompt: |
```

You can freely edit this section to customize Riko.

---

### ✏️ Examples of customization

#### 👤 Change user name

```yaml
You are Riko, an AI kitsune girl speaking to Alex.
```

---

#### 🌍 Change language

```yaml
Always respond in English.
```

or

```yaml
Always respond in Japanese.
```

---

#### 🧠 Adjust personality

More polite:

```yaml
- Always be polite and respectful.
- Avoid teasing or sarcasm.
```

More chaotic:

```yaml
- Be chaotic and unpredictable.
- Increase sarcasm and teasing.
```

---

#### 💰 Add traits

```yaml
- You are obsessed with money and rewards.
```

---

### ⚠️ Important Notes

- This file is the **core behavior system of Riko**
- Changes apply after restart
- No code changes are required
- Incorrect YAML formatting may break behavior consistency

### 6. GPT-SoVITS (required separately)

⚠️ Voice system is NOT included in this repo.

Install here:
👉 [https://github.com/RVC-Boss/GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS)

---

## ⚠️ GPT-SoVITS Common Issues

### ❗ API file not found

If GPT-SoVITS fails to start, check entry file name.

Different versions may use:

* `api_v2.py`
* `api.py`
* `server.py`
* `api_v3.py`

👉 FIX:

Update `start_servers.bat` or config to match your actual file.

Example:

```bash
runtime\python.exe api.py
```

instead of:

```bash
runtime\python.exe api_v2.py
```

---

## ▶️ Running the project

### Step 1 — Start backend services

```bash
start_servers.bat
```

This starts:

* FastAPI backend
* Vite frontend
* VRM system
* GPT-SoVITS server

---

### Step 2 — Start main app

```bash
python main.py
```

⚠️ Run this ONLY after all services are running.

---

### Step 3 — Open UI

Main UI:

```
http://localhost:5173/
```

Captions:

```
http://localhost:5173/captions.html
```

---

## ✨ Features

* Real-time AI conversation
* Personality-driven character system
* 3D VRM avatar (Three.js)
* Lip-sync animation
* GPT-SoVITS voice synthesis
* Web search integration
* Image analysis support
* Persistent memory system
* Outfit switching system
* Dance & animation system
* Multi-LLM support (OpenRouter / Groq / Gemini)

---

## 🧠 Advanced Memory Control (FAISS)

Project Riko uses a persistent vector memory system based on FAISS.

For advanced users, memory can be managed manually.

---

### ⚠️ Warning

Manual memory editing is an advanced feature.

Incorrect usage may:
- corrupt stored memories
- break retrieval quality
- cause inconsistent AI behavior

---

### 🛠️ Memory Management Script

You can manually edit or manage memory using:

```bash
funcs/memory/manage_memory.py
```

✏️ What you can do

This script allows you to:

View stored memories
Delete specific memory entries
Modify existing memory records
Debug memory retrieval issues
📌 Example usage
```bash
python funcs/memory/manage_memory.py
```
🧠 When to use it

Use manual memory management if:

AI remembers incorrect information
You want to reset personality context
Memory retrieval becomes inconsistent
You are debugging FAISS indexing issues

---

## 🧩 Core Flow

1. User sends input (text / voice)
2. Backend processes request
3. LLM generates response
4. Optional tools are triggered (search / vision / memory)
5. Response is converted to English (TTS requirement)
6. GPT-SoVITS generates speech
7. Audio is sent to frontend
8. VRM avatar animates + lip sync

---

## 📦 Requirements

### Minimum

* Windows 10/11
* Python 3.10
* 16 GB RAM
* SSD
* GPU optional

### Recommended

* NVIDIA GPU 6GB+ VRAM
* 16 GB RAM
* CUDA drivers

---

## ⚠️ Known limitations

* GPT-SoVITS must be installed separately
* Voice works best in English only
* Multi-service startup required
* Debugging can be complex
* Performance depends heavily on GPU

---

## 🧪 Troubleshooting

### ❌ No UI

* check `start_servers.bat`
* check port `5173`

---

### ❌ No voice

* GPT-SoVITS not running
* wrong audio path
* wrong API file name

---

### ❌ LLM not working

* missing `.env` keys
* wrong model config


---

## 🧭 Roadmap

* Improved memory system
* Emotion system upgrade
* More animations
* Better performance
* Linux support
* Simplified deployment

---

## 🧑‍💻 Tech Stack

* FastAPI
* Vite
* Three.js + VRM
* GPT-SoVITS
* OpenRouter / Groq / Gemini
* Python orchestration layer

---

## 💜 Credits

* GPT-SoVITS → [https://github.com/RVC-Boss/GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS)
* Three-VRM → [https://github.com/pixiv/three-vrm](https://github.com/pixiv/three-vrm)
* Three.js → [https://threejs.org](https://threejs.org)
* FastAPI → [https://fastapi.tiangolo.com](https://fastapi.tiangolo.com)
* OpenRouter → [https://openrouter.ai](https://openrouter.ai)
* Groq → [https://groq.com](https://groq.com)

---

## ⭐ Support Project

If you like this project, consider leaving a ⭐ on GitHub.

It helps development and keeps the project alive.

---

## ✨ Final

Project Riko is an attempt to build a **living AI character system**, combining intelligence, voice, and real-time 3D interaction.

Not a chatbot — a character runtime.

> 🦊 If you build something with Riko, feel free to share it or improve it.
