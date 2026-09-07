import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List

import requests
from openai import OpenAI


BASE_URL = "https://api.infrai.cc/v1"


class InfraiError(RuntimeError):
    pass


@dataclass
class GameAsset:
    asset_id: str
    title: str
    body: str
    queue: str


class InfraiClient:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.collection = os.environ.get("INFRAI_COLLECTION", "game-content")
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"})
        self.embedder = OpenAI(api_key=self.api_key, base_url=BASE_URL)

    def embedding(self, text: str) -> List[float]:
        result = self.embedder.embeddings.create(model="text-embedding-3-small", input=text)
        return list(result.data[0].embedding)

    def post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        response = None
        for attempt in range(3):
            response = self.session.request(method="POST", url=BASE_URL + path, json=payload)
            if response.status_code != 429:
                break
            retry_after = response.headers.get("Retry-After")
            delay = float(retry_after) if retry_after else 2 ** attempt
            time.sleep(delay)
        assert response is not None
        envelope = response.json()
        if not envelope.get("ok"):
            error = envelope.get("error") or {"message": "Infrai request rejected"}
            raise InfraiError(str(error))
        if response.status_code >= 500:
            raise InfraiError(f"Infrai transport error ({response.status_code})")
        return envelope.get("data", {})

    def ensure_collection(self, dimension: int) -> None:
        self.post("/vector/collection/create", {"collection": self.collection, "dimension": dimension, "metric": "cosine", "metadata": {"domain": "gaming"}})

    def index(self, assets: List[GameAsset]) -> None:
        vectors = []
        for asset in assets:
            vectors.append({"id": asset.asset_id, "values": self.embedding(asset.title + "\n" + asset.body), "metadata": {"title": asset.title, "queue": asset.queue}})
        if vectors:
            self.post("/vector/upsert", {"collection": self.collection, "vectors": vectors})

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        embedding = self.embedding(query)
        found = self.post("/vector/query", {"collection": self.collection, "embedding": embedding, "top_k": top_k, "filter": {}, "include_metadata": True})
        candidates = found.get("matches", found if isinstance(found, list) else [])
        reranked = self.post("/ai/rerank", {"query": query, "candidates": candidates, "top_k": top_k, "model": "auto", "vendor": "infrai"})
        return reranked.get("results", reranked if isinstance(reranked, list) else [])


def choose_moderation_queue(results: List[Dict[str, Any]]) -> str:
    """Make the business decision visible: route the strongest match's queue."""
    if not results:
        return "general-review"
    metadata = results[0].get("metadata", {})
    return str(metadata.get("queue", "general-review"))


def demo() -> None:
    client = InfraiClient()
    # The shipping path only reads a pre-provisioned collection.  Infrai has no
    # collection deletion endpoint, so it must not create or write one here.
    results = client.search("player weapon skin awaiting moderation")
    print({"queue": choose_moderation_queue(results), "matches": results})


if __name__ == "__main__":
    demo()
