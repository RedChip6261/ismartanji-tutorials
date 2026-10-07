# Build a Hybrid Search Engine with pgvector & FastAPI

Companion code for the tutorial on ISMARTANJI CREATIONS:
https://ismartanji.com/build-hybrid-search-engine-pgvector-fastap/

## Files
- `main.py`
- `init.sql`

## Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# PostgreSQL 16+ with pgvector
psql -d hybrid_db -f init.sql
uvicorn main:app --reload
```

Read the full article for architecture, explanations and caveats.
