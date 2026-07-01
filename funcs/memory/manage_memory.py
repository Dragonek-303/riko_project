# funcs/memory/manage_memory.py
"""Tool for previewing and manually editing the FAISS database."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from funcs.memory.vector_memory import VectorMemory


def show_all(memory: VectorMemory):
    """Displays all facts in the database.."""
    print(f"\n=== FAISS database: {len(memory.metadata)} facts ===")
    if not memory.metadata:
        print("(pusta)")
        return
    for i, meta in enumerate(memory.metadata):
        print(f"[{i}] {meta['text']}")


def add_manual(memory, text):
    """Adds the fact manually, ignoring the duplicate filter."""

    saved = memory.add_fact(text, skip_check=True)
    if saved:
        print(f"✅ Added: {saved}")
        memory.save()
    else:
        print("❌ Failed to add the fact.")


def delete_by_index(memory: VectorMemory, index: int):
    """Removes the fact with the specified index."""
    if 0 <= index < len(memory.metadata):
        removed = memory.metadata.pop(index)
        import faiss
        import numpy as np
        new_index = faiss.IndexFlatL2(memory.dim)
        for meta in memory.metadata:
            vec = memory.embedder.encode([meta["text"]]).astype("float32")
            new_index.add(vec)
        memory.index = new_index
        memory.save()
        print(f"🗑 Removed: {removed['text']}")
    else:
        print(f"❌ Invalid index: {index}")


def search(memory: VectorMemory, query: str, top_k: int = 5):
    """Searches for facts similar to the query."""
    results = memory.query(query, top_k=top_k)
    print(f"\n=== Results for: \"{query}\" ===")
    if not results:
        print("(no results)")
        return
    for r in results:
        print(f"  {r}")


def interactive():
    """Interactive memory management console."""
    memory = VectorMemory()
    print("🧠 FAISS memory manager")
    print("Commands: show | add <text> | del <index> | search <text> | Quit")

    while True:
        try:
            cmd = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not cmd:
            continue
        parts = cmd.split(maxsplit=1)
        action = parts[0].lower()

        if action == "quit":
            break
        elif action == "show":
            show_all(memory)
        elif action == "add" and len(parts) > 1:
            add_manual(memory, parts[1])
        elif action == "del" and len(parts) > 1:
            try:
                idx = int(parts[1])
                delete_by_index(memory, idx)
            except ValueError:
                print("❌ Enter the number (index).")
        elif action == "search" and len(parts) > 1:
            search(memory, parts[1])
        else:
            print("❌ Unknown command. Use: show | add <text> | del <index> | search <text>")


if __name__ == "__main__":
    interactive()