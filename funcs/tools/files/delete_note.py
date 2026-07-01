from pathlib import Path

def delete_note():
    """
    Deletes the file data/ai-note/notatka.txt if it exists.
    Returns a dict with the keys 'status' and 'message' (and 'path' on success).
    """
    base_dir = Path("data/ai-note")
    file_path = base_dir / "notatka.txt"

    try:
        if not file_path.exists():
            return {"status": "error", "message": "The file notatka.txt does not exist.."}

        file_path.unlink()
        return {"status": "success", "message": f"File removed: {file_path}", "path": str(file_path)}

    except Exception as e:
        return {"status": "error", "message": str(e)}
