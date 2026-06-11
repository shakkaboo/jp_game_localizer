# Demo: Rolling Memory Localization

This demo walks through the full pipeline using the provided files:

- `context.yaml` — game context for "Echoes of the Forest"
- `script.csv` — 6 Japanese script lines across 2 scenes (village, temple)

## Prerequisites

- Backend installed and dependencies set up (see [README](../README.md))
- `.env` configured with an OpenAI-compatible API key

## Steps

### 1. Start the backend

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

The server starts at `http://localhost:8000`.

### 2. Upload context

```bash
curl -X POST http://localhost:8000/upload/context \
  -F "file=@demo/context.yaml;type=text/yaml"
```

Expected response — a `project_id` is returned (note it for later steps):

```json
{
  "project_id": 1,
  "file_type": "yaml",
  "project": { "title": "Echoes of the Forest", "genre": "Fantasy RPG", ... },
  "sections": ["project", "first_environment", "characters", "relationships", "glossary", "style_rules"],
  "warnings": []
}
```

### 3. Upload script

Use the `project_id` from step 2 (replace `1` if yours differs):

```bash
curl -X POST http://localhost:8000/upload/script/1 \
  -F "file=@demo/script.csv;type=text/csv"
```

Expected response:

```json
{
  "project_id": 1,
  "source_file_id": 1,
  "file_type": "csv",
  "total_lines": 6,
  "detected_characters": ["Kazuki", "Yuki", "Sage Takeno"],
  "detected_scene_hints": ["village", "temple"],
  "warnings": []
}
```

### 4. Create chunks

Chunks group lines by `scene_hint`. Chunk 1 gets initial memory from context.

```bash
curl -X POST http://localhost:8000/chunks/create/1
```

Expected response — 2 chunks, chunk 1 has `previous_memory_json` filled from context:

```json
{
  "project_id": 1,
  "chunks_created": 2,
  "chunks": [
    { "chunk_number": 1, "scene_hint": "village", "lines_count": 3 },
    { "chunk_number": 2, "scene_hint": "temple", "lines_count": 3 }
  ]
}
```

### 5. List chunks

```bash
curl -s http://localhost:8000/chunks/1 | python -m json.tool
```

Note the `id` of each chunk (used in translation step).

### 6. Translate chunk 1 (village)

Replace `<chunk_id_1>` with the ID of the first chunk from step 5.

```bash
curl -s -X POST http://localhost:8000/translate/chunk/<chunk_id_1> | python -m json.tool
```

Expected response — includes `translations_count`, `chunk_memory` with all 7 required fields (chunk_summary, updated_environment, character_states, relationship_updates, tone_to_continue, important_terms, unresolved_hooks), and status `"translated"`.

### 7. Verify chunk 2's previous_memory is filled

```bash
curl -s http://localhost:8000/chunks/detail/<chunk_id_2> | python -m json.tool
```

The `previous_memory_json` field should contain the rolling memory from chunk 1 (same structure as chunk 1's `chunk_memory`).

### 8. Translate chunk 2 (temple)

Replace `<chunk_id_2>` with the ID of the second chunk.

```bash
curl -s -X POST http://localhost:8000/translate/chunk/<chunk_id_2> | python -m json.tool
```

Chunk 2 receives chunk 1's memory as `previous_memory_json`, enabling continuity across scenes.

### 9. Export CSV

```bash
curl -s "http://localhost:8000/export/1?format=csv" -o demo_output.csv
```

Downloads a CSV with columns: `line_id`, `character`, `source_text_ja`, `localized_text_en`, `final_text_en`, `chunk_number`, `chunk_title`, `status`.

### 10. Export JSON

```bash
curl -s "http://localhost:8000/export/1?format=json" | python -m json.tool
```

Returns the same data as a JSON array of objects.

## Expected timeline

| Step | Description | Approx time |
|------|-------------|-------------|
| 1 | Start server | Instant |
| 2-5 | Upload & chunk setup | < 1s |
| 6 | Translate chunk 1 (village, 3 lines) | 2-10s (depends on AI provider) |
| 8 | Translate chunk 2 (temple, 3 lines) | 2-10s |
| 9-10 | Export | Instant |

## Troubleshooting

- **"OPENAI_API_KEY is not set"** — create/edit `.env` with your key
- **502 on translate** — check your API key, base URL, and model; Groq users may need `OPENAI_BASE_URL=https://api.groq.com/openai/v1`
- **Chunk already has translations** — re-translating a chunk deletes old translations and replaces them
- **Port in use** — kill the existing process or change the port in the uvicorn command
