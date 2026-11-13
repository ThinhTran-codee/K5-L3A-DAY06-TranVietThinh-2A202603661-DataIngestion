"""Store and search vectors using PostgreSQL + pgvector."""
import json
from typing import Any
import psycopg
from .models import Chunk


class PgVectorStore:
    def __init__(self, database_url: str, dimensions: int = 1536) -> None:
        self.database_url = database_url
        self.dimensions = dimensions

    def _get_connection(self):
        return psycopg.connect(self.database_url)

    def create_schema(self) -> None:
        """Create extension and chunks table with metadata JSONB and vector columns."""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS chunks (
                        id TEXT PRIMARY KEY,
                        strategy TEXT NOT NULL,
                        chunk_id TEXT NOT NULL,
                        document_id TEXT NOT NULL,
                        source TEXT NOT NULL,
                        page INT NOT NULL,
                        text TEXT NOT NULL,
                        metadata JSONB NOT NULL,
                        embedding vector({self.dimensions}) NOT NULL
                    );
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chunks_strategy ON chunks(strategy);
                """)
            conn.commit()

    def upsert(self, strategy: str, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        """Store chunks and embeddings. Clean previous strategy data to prevent duplication."""
        if len(chunks) != len(vectors):
            raise ValueError(f"Mismatch: {len(chunks)} chunks vs {len(vectors)} vectors")

        self.create_schema()

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                # Remove obsolete chunks for this strategy to ensure idempotence
                cur.execute("DELETE FROM chunks WHERE strategy = %s;", (strategy,))

                # Prepare records
                records = []
                for chunk, vec in zip(chunks, vectors):
                    unique_id = f"{strategy}::{chunk.chunk_id}"
                    vec_str = "[" + ",".join(str(v) for v in vec) + "]"
                    meta_json = json.dumps(chunk.metadata)
                    records.append((
                        unique_id,
                        strategy,
                        chunk.chunk_id,
                        chunk.document_id,
                        chunk.source,
                        chunk.page,
                        chunk.text,
                        meta_json,
                        vec_str
                    ))

                # Batch insert
                cur.executemany(f"""
                    INSERT INTO chunks (id, strategy, chunk_id, document_id, source, page, text, metadata, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::vector({self.dimensions}))
                """, records)
            conn.commit()

    def search(
        self,
        strategy: str,
        query_vector: list[float],
        top_k: int = 3,
        filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Search top-k most similar chunks by cosine distance, optionally filtering on metadata."""
        vec_str = "[" + ",".join(str(v) for v in query_vector) + "]"
        sql_conditions = ["strategy = %s"]
        where_params: list[Any] = [strategy]

        if filters:
            for k, v in filters.items():
                sql_conditions.append("metadata->>%s = %s")
                where_params.extend([k, str(v)])

        where_clause = " AND ".join(sql_conditions)
        # Parameter order: SELECT vec, WHERE params, ORDER BY vec, LIMIT top_k
        params = [vec_str] + where_params + [vec_str, top_k]

        sql = f"""
            SELECT chunk_id, document_id, source, page, text, metadata,
                   1 - (embedding <=> %s::vector({self.dimensions})) AS score
            FROM chunks
            WHERE {where_clause}
            ORDER BY embedding <=> %s::vector({self.dimensions}) ASC
            LIMIT %s;
        """

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()

        results = []
        for r in rows:
            meta = r[5]
            if isinstance(meta, str):
                meta = json.loads(meta)
            results.append({
                "chunk_id": r[0],
                "document_id": r[1],
                "source": r[2],
                "page": r[3],
                "text": r[4],
                "metadata": meta,
                "score": float(r[6])
            })
        return results
