"""OpenAI real embedding provider adapter with persistent local cache."""
import hashlib
import json
import os
from pathlib import Path
from typing import Protocol
from dotenv import load_dotenv
from openai import OpenAI


class Embedder(Protocol):
    model_name: str
    dimensions: int

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per input text, in the same order."""
        ...

    def embed_query(self, question: str) -> list[float]:
        """Return a query vector compatible with the stored document vectors."""
        ...


class MyEmbedder:
    """OpenAI embedding implementation with persistent local caching to guarantee reproducibility and speed."""

    def __init__(self, model_name: str = "text-embedding-3-small", cache_path: str = "starter/results/.embedding_cache.json") -> None:
        load_dotenv(Path(__file__).resolve().parents[1] / ".env")
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY missing: provide it in starter/.env")
        
        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name or "text-embedding-3-small"
        self.dimensions = 1536
        self.cache_path = Path(cache_path)
        self.cache: dict[str, list[float]] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        if self.cache_path.exists():
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    self.cache = json.load(f)
            except Exception:
                self.cache = {}

    def _save_cache(self) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(self.cache, f)

    def _hash_text(self, text: str) -> str:
        key = f"{self.model_name}::{text}"
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def embed_documents(self, texts: list[str], batch_size: int = 64) -> list[list[float]]:
        results: list[list[float] | None] = [None] * len(texts)
        missing_indices: list[int] = []
        missing_texts: list[str] = []

        # Check cache first
        for i, text in enumerate(texts):
            h = self._hash_text(text)
            if h in self.cache:
                results[i] = self.cache[h]
            else:
                missing_indices.append(i)
                missing_texts.append(text)

        # Batch embed missing texts
        if missing_texts:
            print(f"Embedding {len(missing_texts)} new texts using {self.model_name}...")
            for b in range(0, len(missing_texts), batch_size):
                batch_t = missing_texts[b:b + batch_size]
                response = self.client.embeddings.create(input=batch_t, model=self.model_name)
                for item_idx, emb_data in enumerate(response.data):
                    original_idx = missing_indices[b + item_idx]
                    vec = emb_data.embedding
                    results[original_idx] = vec
                    self.cache[self._hash_text(batch_t[item_idx])] = vec
            self._save_cache()

        return [r for r in results if r is not None]

    def embed_query(self, question: str) -> list[float]:
        h = self._hash_text(question)
        if h in self.cache:
            return self.cache[h]
        
        response = self.client.embeddings.create(input=question, model=self.model_name)
        vec = response.data[0].embedding
        self.cache[h] = vec
        self._save_cache()
        return vec
