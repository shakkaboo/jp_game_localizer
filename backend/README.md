# JP Game Localizer MVP — Backend

Japanese-to-English game localization backend powered by FastAPI, SQLite, and scene-based rolling memory.

## Setup

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy environment config
cp .env.example .env

# 4. Run the server
uvicorn app.main:app --reload
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/projects` | Create a new project |
| `GET` | `/projects` | List all projects |
| `GET` | `/projects/{id}` | Get a single project |
| `POST` | `/upload/context?project_id=1` | Upload a context file |
| `POST` | `/upload/script?project_id=1` | Upload a script file |
| `POST` | `/chunks/generate` | Generate scene chunks from uploaded script |
| `GET` | `/chunks/?project_id=1` | List chunks for a project |
| `GET` | `/chunks/{id}` | Get a single chunk |
| `GET` | `/translate/{chunk_id}` | List translations for a chunk |
| `PATCH` | `/translate/{translation_id}` | Edit a translation |
| `POST` | `/export/` | Export localized script (CSV or JSON) |

## Project workflow

1. `POST /projects` → get a `project_id`
2. `POST /upload/context?project_id=1` → upload game context (JSON, YAML, TXT, DOCX)
3. `POST /upload/script?project_id=1` → upload Japanese script (CSV, XLSX, TXT, JSON)
4. `POST /chunks/generate` → auto-group script lines into scene chunks
5. *(AI translation not yet implemented — planned)*
6. `POST /export/` → download localized script

## Supported file formats

**Scripts:** CSV, XLSX, TXT, JSON  
**Context:** JSON, YAML, TXT, DOCX
