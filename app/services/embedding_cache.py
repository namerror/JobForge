import logging
from pathlib import Path
import json

logger = logging.getLogger("embedding_cache")

class EmbeddingCache:
    def __init__(self, model: str):
        self._ROLE_EMB_CACHE_DIR = Path(__file__).parent.parent / "data" / "embeddings" / model / "role_cache.json"
        self._SKILL_EMB_CACHE_DIR = Path(__file__).parent.parent / "data" / "embeddings" / model / "skill_cache.json"
        self.role_cache, self.skill_cache = self._load_embeddings_cache()

    def _load_embeddings_cache(self) -> tuple[dict, dict]:
        # load role
        try:
            with open(self._ROLE_EMB_CACHE_DIR) as f:
                self.role_cache = json.load(f)
        except FileNotFoundError:
            logger.warning(
                "role_embedding_cache_not_found",
                extra={"event": "role_embedding_cache_not_found", "cache_path": str(self._ROLE_EMB_CACHE_DIR)},
            )
            self.role_cache = {}
        
        # load skill
        try:
            with open(self._SKILL_EMB_CACHE_DIR) as f:
                self.skill_cache = json.load(f)
        except FileNotFoundError:
            logger.warning(
                "skill_embedding_cache_not_found",
                extra={"event": "skill_embedding_cache_not_found", "cache_path": str(self._SKILL_EMB_CACHE_DIR)},
            )
            self.skill_cache = {}

        return self.role_cache, self.skill_cache


    def cache_lookup(self, text: str, type: str) -> list[float] | None:
        if type == 'role':
            return self.role_cache.get(text)
        elif type == 'skill':
            return self.skill_cache.get(text)
        else:
            raise ValueError(f"Invalid cache type: {type}")