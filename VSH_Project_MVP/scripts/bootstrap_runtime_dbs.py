from __future__ import annotations

import json
import uuid
from pathlib import Path

from chromadb import PersistentClient
from chromadb.utils import embedding_functions

from config import (
    CHROMA_COLLECTION,
    CHROMA_DB_DIR,
    FIX_PATH,
    KNOWLEDGE_PATH,
    SEED_DB_DIR,
)
from shared.vulnerability_db import VulnerabilityDatabase


def _load_seed_json(name: str) -> list[dict]:
    path = SEED_DB_DIR / name
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _sync_seed_files() -> None:
    Path(KNOWLEDGE_PATH).write_text(
        json.dumps(_load_seed_json("knowledge.json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    Path(FIX_PATH).write_text(
        json.dumps(_load_seed_json("kisa_fix.json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _build_chroma() -> None:
    client = PersistentClient(path=str(CHROMA_DB_DIR))
    ef = embedding_functions.DefaultEmbeddingFunction()
    collection = client.get_or_create_collection(name=CHROMA_COLLECTION, embedding_function=ef)

    existing = collection.count()
    if existing:
        ids = collection.get(include=[])["ids"]
        if ids:
            collection.delete(ids=ids)

    docs = []
    metadatas = []
    ids = []

    for item in _load_seed_json("knowledge.json"):
        docs.append(item.get("description", ""))
        metadatas.append(
            {
                "cwe": item.get("id", ""),
                "source": "KISA",
                "source_id": item.get("reference", ""),
                "title": item.get("name", ""),
                "kisa_article": item.get("reference", ""),
                "text": item.get("description", ""),
            }
        )
        ids.append(f"knowledge-{item.get('id', uuid.uuid4().hex)}")

    for item in _load_seed_json("kisa_fix.json"):
        docs.append(item.get("description", ""))
        metadatas.append(
            {
                "cwe": item.get("id", ""),
                "source": "KISA_FIX",
                "source_id": item.get("id", ""),
                "title": f"Fix guide for {item.get('id', '')}",
                "kisa_article": item.get("id", ""),
                "text": item.get("description", ""),
            }
        )
        ids.append(f"fix-{item.get('id', uuid.uuid4().hex)}")

    if docs:
        collection.add(ids=ids, documents=docs, metadatas=metadatas)


def main() -> None:
    _sync_seed_files()
    db = VulnerabilityDatabase()
    db.load_mock_data()
    db.close()
    _build_chroma()
    print("Runtime databases bootstrapped successfully.")


if __name__ == "__main__":
    main()
