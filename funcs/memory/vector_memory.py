# funcs/memory/vector_memory.py
import pickle
from pathlib import Path
from datetime import datetime
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# Global singleton for the embedding model
_embedder = None

def _get_embedder(model_name: str = "sdadas/st-polish-paraphrase-from-mpnet"):
    """Loads the embedding model only once."""
    global _embedder
    if _embedder is None:
        print(f"🔄 Loading embedding model: {model_name} (first and only load)...")
        _embedder = SentenceTransformer(model_name)
        print("✅ The embedding model is ready.")
    return _embedder


class VectorMemory:
    """Long-term memory store based on FAISS and a Polish embedding model."""

    def __init__(self, model_name: str = "intfloat/multilingual-e5-large"):
        cache_dir = Path("data/vector_memory")
        cache_dir.mkdir(parents=True, exist_ok=True)

        self.index_path = cache_dir / "memory.index"
        self.meta_path = cache_dir / "memory_meta.pkl"

        self.embedder = _get_embedder(model_name)
        try:
            self.dim = self.embedder.get_embedding_dimension()
        except AttributeError:
            self.dim = self.embedder.get_sentence_embedding_dimension()

        # Initializing or loading the FAISS index and metadata
        if self.index_path.exists() and self.meta_path.exists():
            self.index = faiss.read_index(str(self.index_path))
            with open(self.meta_path, "rb") as f:
                self.metadata = pickle.load(f)
        else:
            self.index = faiss.IndexFlatL2(self.dim)
            self.metadata = []

    def add_fact(self, text: str, similarity_threshold: float = 0.92, skip_check: bool = False) -> str | None:
        """It adds the fact. It indexes the plain text, with the timestamp stored only in the metadata."""
        if not skip_check and self.index.ntotal > 0:
            query_vec = self.embedder.encode([text]).astype("float32")
            norm = np.linalg.norm(query_vec)
            if norm > 0:
                query_vec = query_vec / norm

            D, I = self.index.search(query_vec, 1)

            if len(D[0]) > 0 and I[0][0] < len(self.metadata):
                existing_text = self.metadata[I[0][0]]["text"]
                clean_existing = existing_text.split("] ", 1)[-1] if "] " in existing_text else existing_text
                existing_vec = self.embedder.encode([clean_existing]).astype("float32")
                norm_ex = np.linalg.norm(existing_vec)
                if norm_ex > 0:
                    existing_vec = existing_vec / norm_ex

                cos_sim = np.dot(query_vec[0], existing_vec[0])
                if cos_sim >= similarity_threshold:
                    print(f"⏭️ [FAISS SKIP] A fact too similar to an existing one (sim: {cos_sim:.3f}): {text[:60]}...")
                    return None

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_text = f"[{timestamp}] {text}"

        vector = self.embedder.encode([text]).astype("float32")
        self.index.add(vector)
        self.metadata.append({"text": full_text, "timestamp": timestamp})
        return full_text

    def query(self, query_text: str, top_k: int = 5) -> list:
        if self.index.ntotal == 0:
            return []
        # For E5/Stella models, add a prefix "query: "
        vec = self.embedder.encode([f"query: {query_text}"]).astype("float32")
        distances, indices = self.index.search(vec, top_k)
        results = []
        for idx in indices[0]:
            if idx < len(self.metadata):
                results.append(self.metadata[idx]["text"])
        return results

    def get_context_block(self, query_text: str, top_k: int = 5) -> str:
        """Returns a ready-made memory block formatted for the prompt."""
        facts = self.query(query_text, top_k)
        if not facts:
            return ""
        return "\n".join(f"- {f}" for f in facts)

    def save(self):
        """Saves the FAISS index and metadata to disk."""
        faiss.write_index(self.index, str(self.index_path))
        with open(self.meta_path, "wb") as f:
            pickle.dump(self.metadata, f)