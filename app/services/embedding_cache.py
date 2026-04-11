import json
import logging
import os
from pathlib import Path

from app.config import settings

logger = logging.getLogger("embedding_cache")

class EmbeddingCache:
    def __init__(self, model: str):
        self._ROLE_EMB_CACHE_DIR = Path(__file__).parent.parent / "data" / "embeddings" / model / "role_cache.json"
        self._SKILL_EMB_CACHE_DIR = Path(__file__).parent.parent / "data" / "embeddings" / model / "skill_cache.json"
        self.model = model
        self.dimensions = getattr(settings, "EMBEDDING_DIMENSIONS", None)
        self.role_cache, self.skill_cache = self._load_embeddings_cache()

    def _load_embeddings_cache(self) -> tuple[dict, dict]:
        model = getattr(self, "model", None)
        dimensions = getattr(self, "dimensions", None)

        # load role
        try:
            with open(self._ROLE_EMB_CACHE_DIR) as f:
                self.role_cache = self._parse_cache_payload(json.load(f), model, dimensions)
        except FileNotFoundError:
            logger.warning(
                "role_embedding_cache_not_found",
                extra={"event": "role_embedding_cache_not_found", "cache_path": str(self._ROLE_EMB_CACHE_DIR)},
            )
            self.role_cache = {}
        
        # load skill
        try:
            with open(self._SKILL_EMB_CACHE_DIR) as f:
                self.skill_cache = self._parse_cache_payload(json.load(f), model, dimensions)
        except FileNotFoundError:
            logger.warning(
                "skill_embedding_cache_not_found",
                extra={"event": "skill_embedding_cache_not_found", "cache_path": str(self._SKILL_EMB_CACHE_DIR)},
            )
            self.skill_cache = {}

        return self.role_cache, self.skill_cache

    def _parse_cache_payload(self, payload: dict, model: str | None, dimensions: int | None) -> dict:
        if "data" not in payload:
            # Backwards compatibility: old format was a raw dict mapping text -> embedding
            return payload

        payload_model = payload.get("model")
        payload_dimensions = payload.get("dimensions")
        if model is not None and payload_model != model:
            logger.warning(
                "embedding_cache_model_mismatch",
                extra={"event": "embedding_cache_model_mismatch", "expected": model, "found": payload_model},
            )
            return {}
        if dimensions is not None and dimensions != payload_dimensions:
            logger.warning(
                "embedding_cache_dimensions_mismatch",
                extra={"event": "embedding_cache_dimensions_mismatch", "expected": dimensions, "found": payload_dimensions},
            )
            return {}

        return payload.get("data", {})

    def _cache_payload(self, data: dict) -> dict:
        return {
            "version": 1,
            "model": self.model,
            "dimensions": self.dimensions,
            "data": data,
        }

    def _atomic_write_json(self, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        with open(tmp_path, "w") as f:
            json.dump(payload, f, sort_keys=True)
        os.replace(tmp_path, path)

    def _store_role_cache(self) -> None:
        self._atomic_write_json(self._ROLE_EMB_CACHE_DIR, self._cache_payload(self.role_cache))

    def _store_skill_cache(self) -> None:
        self._atomic_write_json(self._SKILL_EMB_CACHE_DIR, self._cache_payload(self.skill_cache))
    
    def cache_store(self, text: str, embedding: list[float], type: str) -> None:
        if type == 'role':
            self.role_cache[text] = embedding
            self._store_role_cache()
        elif type == 'skill':
            self.skill_cache[text] = embedding
            self._store_skill_cache()
        else:
            raise ValueError(f"Invalid cache type: {type}")

    def cache_lookup(self, text: str, type: str) -> list[float] | None:
        if type == 'role':
            return self.role_cache.get(text)
        elif type == 'skill':
            return self.skill_cache.get(text)
        else:
            raise ValueError(f"Invalid cache type: {type}")
