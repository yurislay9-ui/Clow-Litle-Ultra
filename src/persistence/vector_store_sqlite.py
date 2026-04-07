#!/usr/bin/env python3
"""
VectorStoreSQLite - Almacenamiento Vectorial en SQLite.
"""

import sqlite3
import json
import math
from typing import List, Dict, Any, Optional, Tuple, Union


class VectorStoreSQLite:
    """Almacén de vectores en SQLite con búsqueda por similitud."""

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS vectors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vector_data TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def add_vector(self, vector: List[float], metadata: Optional[Dict[str, Any]] = None) -> int:
        vector_json = json.dumps(vector)
        metadata_json = json.dumps(metadata) if metadata else None
        cursor = self.conn.execute(
            "INSERT INTO vectors (vector_data, metadata) VALUES (?, ?)",
            (vector_json, metadata_json)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_vector(self, vector_id: Union[int, str]) -> Tuple[Optional[List[float]], Optional[Dict[str, Any]]]:
        row = self.conn.execute(
            "SELECT vector_data, metadata FROM vectors WHERE id = ?",
            (int(vector_id),)
        ).fetchone()
        if row is None:
            return None, None
        vector = json.loads(row["vector_data"])
        metadata = json.loads(row["metadata"]) if row["metadata"] else None
        return vector, metadata

    def delete_vector(self, vector_id: Union[int, str]) -> bool:
        result = self.conn.execute(
            "DELETE FROM vectors WHERE id = ?",
            (int(vector_id),)
        )
        self.conn.commit()
        return result.rowcount > 0

    def update_vector(self, vector_id: Union[int, str], vector: List[float],
                      metadata: Optional[Dict[str, Any]] = None) -> bool:
        vector_json = json.dumps(vector)
        metadata_json = json.dumps(metadata) if metadata else None
        result = self.conn.execute(
            "UPDATE vectors SET vector_data = ?, metadata = ? WHERE id = ?",
            (vector_json, metadata_json, int(vector_id))
        )
        self.conn.commit()
        return result.rowcount > 0

    def search(self, query_vector: List[float], k: int = 5) -> List[Dict[str, Any]]:
        cursor = self.conn.execute("SELECT id, vector_data, metadata FROM vectors")
        rows = cursor.fetchall()
        results = []
        for row in rows:
            vector = json.loads(row["vector_data"])
            similarity = self._cosine_similarity(query_vector, vector)
            metadata = json.loads(row["metadata"]) if row["metadata"] else None
            results.append({
                "id": row["id"],
                "vector": vector,
                "metadata": metadata,
                "similarity": similarity
            })
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:k]

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        if len(a) != len(b):
            return 0.0
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)

    def get_stats(self) -> Dict[str, Any]:
        count = self.conn.execute("SELECT COUNT(*) as count FROM vectors").fetchone()["count"]
        return {
            "total_vectors": count,
            "db_path": self.db_path,
            "in_memory": self.db_path == ":memory:"
        }

    def clear(self):
        self.conn.execute("DELETE FROM vectors")
        self.conn.commit()

    def close(self):
        if self.conn:
            self.conn.close()

    def __del__(self):
        self.close()

    def __len__(self) -> int:
        return self.conn.execute("SELECT COUNT(*) as count FROM vectors").fetchone()["count"]
