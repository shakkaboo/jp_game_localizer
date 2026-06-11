# JP Game Localizer MVP — Backend

Japanese-to-English game localization backend powered by FastAPI, SQLite, and scene-based rolling memory. No frontend, no auth, no vector DB.

The pipeline:
1. Upload game **context** (world, characters, glossary, style rules)
2. Upload a Japanese **script** (multi-format: CSV, XLSX, TXT, JSON)
3. Auto-group lines into **scene chunks**
4. Translate each chunk via an OpenAI-compatible LLM with **rolling memory**
5. **Export** the localized script as CSV or JSON

## Supported file formats

| Type | Formats |
|------|---------|
| Context | JSON, YAML, TXT, DOCX |
| Script | CSV, XLSX, TXT (colon-delimited), JSON (array or key-value) |

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then edit .env with your API key
uvicorn app.main:app --reload
```

> **Do not commit `.env`** — it contains your API key. `.env` is in `.gitignore`.

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | _(empty)_ | API key for OpenAI-compatible provider |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | Base URL (use `https://api.groq.com/openai/v1` for Groq) |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model name (e.g. `llama-3.1-8b-instant` for Groq) |
| `DATABASE_URL` | `sqlite:///./localizer.db` | Database connection string |
| `DEBUG` | `true` | Enable debug mode |

### Groq / OpenAI-compatible setup

For **Groq**:

```bash
OPENAI_API_KEY=gsk_your_key
OPENAI_BASE_URL=https://api.groq.com/openai/v1
OPENAI_MODEL=llama-3.1-8b-instant
```

For **OpenAI** (defaults work as-is):

```bash
OPENAI_API_KEY=sk-your-key
# OPENAI_BASE_URL and OPENAI_MODEL can stay at defaults
```

> The AI client retries without `response_format` on token-limit or JSON failures, which improves compatibility with providers that have partial JSON mode support.

## Demo

See [demo/run_demo.md](demo/run_demo.md) for a complete walkthrough with sample files.

```bash
cd backend       # from project root
source venv/bin/activate
uvicorn app.main:app --reload
```

### Full curl flow

```bash
# 1. Upload context
curl -X POST http://localhost:8000/upload/context \
  -F "file=@demo/context.yaml;type=text/yaml"

# 2. Upload script (replace 1 with your project_id)
curl -X POST http://localhost:8000/upload/script/1 \
  -F "file=@demo/script.csv;type=text/csv"

# 3. Create chunks
curl -X POST http://localhost:8000/chunks/create/1

# 4. List chunks (note the chunk IDs)
curl -s http://localhost:8000/chunks/1 | python -m json.tool

# 5. Translate chunk 1 (replace <id>)
curl -s -X POST http://localhost:8000/translate/chunk/<id> | python -m json.tool

# 6. Verify rolling memory propagated to chunk 2 (replace <id>)
curl -s http://localhost:8000/chunks/detail/<id> | python -m json.tool

# 7. Translate chunk 2 (replace <id>)
curl -s -X POST http://localhost:8000/translate/chunk/<id> | python -m json.tool

# 8. Export localized script
curl -s "http://localhost:8000/export/1?format=csv" -o output.csv
curl -s "http://localhost:8000/export/1?format=json" | python -m json.tool
```

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/projects` | Create a new project |
| `GET` | `/projects` | List all projects |
| `GET` | `/projects/{id}` | Get a single project |
| `GET` | `/projects/{id}/context` | Get context for a project |
| `POST` | `/upload/context` | Upload a context file (auto-creates project if no `project_id`) |
| `POST` | `/upload/script/{project_id}` | Upload a script file to a project |
| `POST` | `/chunks/create/{project_id}` | Group script lines into scene chunks |
| `GET` | `/chunks/{project_id}` | List chunks for a project |
| `GET` | `/chunks/detail/{chunk_id}` | Get chunk detail with lines and translations |
| `POST` | `/translate/chunk/{chunk_id}` | Translate a chunk via AI |
| `GET` | `/translate/{chunk_id}` | List translations for a chunk |
| `PATCH` | `/translate/{translation_id}` | Edit a single translation by ID |
| `GET` | `/export/{project_id}?format=csv` | Export script as CSV |
| `GET` | `/export/{project_id}?format=json` | Export script as JSON |

## Architecture

```
upload/script  ──> parser ──> normalizer ──> SourceLine rows
upload/context ──> parser ──> normalizer ──> ContextData row (JSON)
chunks/create  ──> chunker ──> Chunk rows (grouped by scene_hint)
translate      ──> prompt builder ──> AI call ──> Translation rows + Chunk memory
export         ──> join translations + source lines ──> CSV / JSON
```

- **Chunk 1** gets initial memory from context (`first_environment`, characters, glossary)
- **Each subsequent chunk** receives the previous chunk's `chunk_memory` as rolling context
- **If AI memory is incomplete**, the backend generates safe fallback values from source lines, translations, and previous memory
- No hardcoded game data in application logic — everything comes from uploaded files

## Project structure

```
backend/
├── app/
│   ├── main.py                   # FastAPI app, CORS, startup
│   ├── database.py               # SQLAlchemy engine + session
│   ├── models.py                 # 6 SQLAlchemy models
│   ├── schemas.py                # Pydantic request/response schemas
│   ├── ai/
│   │   ├── llm_client.py         # OpenAI-compatible API client with retry
│   │   └── prompts.py            # System + user prompt builders
│   ├── routes/
│   │   ├── upload.py             # Context & script upload endpoints
│   │   ├── chunks.py             # Chunk create/list/detail endpoints
│   │   ├── translate.py          # Translate + list + patch endpoints
│   │   └── export.py             # CSV / JSON export endpoint
│   └── services/
│       ├── file_detector.py      # File type detection by extension
│       ├── script_parser.py      # CSV, XLSX, TXT, JSON parsers
│       ├── context_parser.py     # JSON, YAML, TXT, DOCX parsers
│       ├── normalizer.py         # Column alias resolution + warnings
│       ├── chunker.py            # Scene-based line grouping
│       ├── memory_service.py     # Initial + rolling memory validation
│       └── export_service.py     # Join + serialize translations
├── demo/
│   ├── context.yaml              # Sample game context
│   ├── script.csv                # Sample Japanese script
│   └── run_demo.md               # Step-by-step demo guide
├── requirements.txt
├── .env.example
└── .env                          # (gitignored — your API key here)
```
