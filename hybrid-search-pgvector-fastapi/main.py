"""
Production Hybrid Search Engine using PostgreSQL, pgvector, and FastAPI.
Tested with Python 3.11+, PostgreSQL 16, pgvector 0.7+, and SQLAlchemy 2.0.30.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, List, Optional

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Database Configuration
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/hybrid_db"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

# Async Engine and Session Pool
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_recycle=1800,
    pool_pre_ping=True,
)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


class EmbeddingService:
    """
    Manages local neural sentence embeddings using SentenceTransformers.
    """
    def __init__(self, model_name: str) -> None:
        logger.info("Loading embedding model: %s", model_name)
        self.model = SentenceTransformer(model_name)

    def embed_text(self, text_input: str) -> List[float]:
        return self.model.encode(text_input, normalize_embeddings=True).tolist()


# Global Singleton for Embedding Generation
embedding_service = EmbeddingService(EMBEDDING_MODEL_NAME)


# Pydantic Schemas
class DocumentIngest(BaseModel):
    title: str = Field(..., max_length=255)
    content: str = Field(..., min_length=1)


class SearchQuery(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(default=10, ge=1, le=50)
    rrf_k: int = Field(default=60, ge=1, le=100)


class SearchResult(BaseModel):
    id: int
    title: str
    content: str
    rrf_score: float
    lexical_rank: Optional[int]
    vector_rank: Optional[int]


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize table and indexes on startup
    logger.info("Verifying database schema and HNSW/GIN indexes...")
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        await conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                tsv TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', title || ' ' || content)) STORED,
                embedding VECTOR({EMBEDDING_DIM})
            );
        """))
        # GIN Index for fast Lexical Full-Text Search
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_documents_tsv ON documents USING GIN(tsv);
        """))
        # HNSW Index for fast Vector Similarity Search
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_documents_hnsw 
            ON documents USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64);
        """))
    logger.info("Database schema verification complete.")
    yield
    await engine.dispose()
    logger.info("Database connection pools closed.")


app = FastAPI(title="Production Hybrid Search Engine", lifespan=lifespan)


@app.post("/documents", status_code=status.HTTP_201_CREATED)
async def ingest_document(
    doc: DocumentIngest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Ingests raw text, generates dense vector embedding, and stores records in PostgreSQL.
    """
    try:
        combined_text = f"{doc.title} {doc.content}"
        vector = embedding_service.embed_text(combined_text)

        insert_sql = text("""
            INSERT INTO documents (title, content, embedding)
            VALUES (:title, :content, :embedding)
            RETURNING id;
        """)
        
        result = await db.execute(
            insert_sql,
            {"title": doc.title, "content": doc.content, "embedding": str(vector)},
        )
        await db.commit()
        doc_id = result.scalar()
        return {"id": doc_id, "status": "indexed"}
    except Exception as err:
        await db.rollback()
        logger.error("Failed to index document: %s", err)
        raise HTTPException(status_code=500, detail="Database indexing error")


@app.post("/search", response_model=List[SearchResult])
async def search_documents(
    payload: SearchQuery,
    db: AsyncSession = Depends(get_db),
) -> List[SearchResult]:
    """
    Executes parallel lexical and vector search with Reciprocal Rank Fusion (RRF) inside PostgreSQL.
    """
    try:
        query_vector = embedding_service.embed_text(payload.query)

        # Unified RRF Query utilizing Common Table Expressions (CTEs)
        hybrid_sql = text(f"""
            WITH lexical_search AS (
                SELECT 
                    id,
                    ROW_NUMBER() OVER (ORDER BY ts_rank_cd(tsv, plainto_tsquery('english', :query)) DESC) AS rank
                FROM documents
                WHERE tsv @@ plainto_tsquery('english', :query)
                LIMIT 50
            ),
            vector_search AS (
                SELECT 
                    id,
                    ROW_NUMBER() OVER (ORDER BY embedding <=> :vector) AS rank
                FROM documents
                ORDER BY embedding <=> :vector
                LIMIT 50
            ),
            combined_scores AS (
                SELECT 
                    COALESCE(l.id, v.id) AS id,
                    COALESCE(1.0 / (:k + l.rank), 0.0) + COALESCE(1.0 / (:k + v.rank), 0.0) AS rrf_score,
                    l.rank AS lexical_rank,
                    v.rank AS vector_rank
                FROM lexical_search l
                FULL OUTER JOIN vector_search v ON l.id = v.id
            )
            SELECT 
                d.id,
                d.title,
                d.content,
                c.rrf_score,
                c.lexical_rank,
                c.vector_rank
            FROM combined_scores c
            JOIN documents d ON c.id = d.id
            ORDER BY c.rrf_score DESC
            LIMIT :limit;
        """)

        result = await db.execute(
            hybrid_sql,
            {
                "query": payload.query,
                "vector": str(query_vector),
                "k": payload.rrf_k,
                "limit": payload.limit,
            },
        )
        
        rows = result.fetchall()
        return [
            SearchResult(
                id=row.id,
                title=row.title,
                content=row.content,
                rrf_score=float(row.rrf_score),
                lexical_rank=row.lexical_rank,
                vector_rank=row.vector_rank,
            )
            for row in rows
        ]
    except Exception as err:
        logger.error("Hybrid search query failed: %s", err)
        raise HTTPException(status_code=500, detail="Search query execution failed")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
