from pathlib import Path

def save_note(content: str):
    """
    Saves the content to the file data/ai-note/notatka.txt
    """
    base_dir = Path("data/ai-note")
    base_dir.mkdir(parents=True, exist_ok=True)

    file_path = base_dir / "notatka.txt"

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return {
            "status": "success",
            "message": f"File saved: {file_path}",
            "path": str(file_path)
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}
