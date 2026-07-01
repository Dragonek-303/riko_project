from pathlib import Path

def append_note(content: str):
    """
    Appends content to the file data/ai-note/notatka.txt
    Automatically adds a space and a new line.
    """
    base_dir = Path("data/ai-note")
    base_dir.mkdir(parents=True, exist_ok=True)

    file_path = base_dir / "notatka.txt"

    try:
        # If the file exists and is not empty → add an empty line as a separator
        if file_path.exists() and file_path.stat().st_size > 0:
            separator = "\n"
        else:
            separator = ""

        with open(file_path, "a", encoding="utf-8") as f:
            f.write(separator + content.strip() + "\n")

        return {
            "status": "success",
            "message": f"Content has been appended to the file: {file_path}",
            "path": str(file_path)
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}
