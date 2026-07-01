from pathlib import Path

def read_note():
    """
    Reads the content of the file data/ai-note/notatka.txt
    """
    file_path = Path("data/ai-note/notatka.txt")

    if not file_path.exists():
        return {
            "status": "error",
            "message": "The file notatka.txt does not exist yet."
        }

    try:
        content = file_path.read_text(encoding="utf-8")
        return {
            "status": "success",
            "content": content
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}
