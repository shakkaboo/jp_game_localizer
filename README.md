# JP Game Localizer MVP

A full-stack Japanese-to-English game localization MVP with a **FastAPI backend**, **Next.js frontend**, **SQLite database**, and **scene-based rolling memory**.

Upload your game context and Japanese script, auto-group lines into scene chunks, translate using any OpenAI-compatible LLM provider, review and edit the output, then export the localized script as CSV or JSON.

Built as a portfolio project demonstrating full-stack engineering, AI integration, file parsing, prompt engineering, and context-aware localization workflow design.

---

## Why This Is Different

Normal LLM translation tools often treat each line in isolation. They may not understand the scene, the characters, the relationship dynamics, glossary terms, or what happened in the previous scene.

This project is designed specifically for game localization.

It:

* Groups script lines into **scene chunks** so the LLM sees complete dramatic units
* Injects **game context** such as characters, glossary, relationships, and style rules into translation prompts
* Passes **rolling memory** from one chunk to the next so the model remembers recent events
* Validates and fills **incomplete AI memory** automatically so continuity does not break
* Allows human review through editable `final_text_en` output
* Exports translation results in workflow-friendly CSV or JSON format

The goal is to produce localized output that preserves:

* Character voice
* Story continuity
* Scene context
* Relationship dynamics
* Glossary consistency
* Natural English dialogue

No game data is hardcoded. Everything comes from uploaded context and script files.

---

## Features

* **Multi-format upload** for context and script files
* **Context-aware translation** using world, character, glossary, and style information
* **Scene chunking** using `scene_hint`
* **Rolling story memory** between chunks
* **Memory validation and fallback** when AI memory output is incomplete
* **Editable review workflow** for human correction
* **CSV and JSON export**
* **OpenAI-compatible LLM support**
* **Groq API support**
* **FastAPI backend**
* **Next.js frontend**
* **SQLite local storage**

---

## Supported Input Formats

| Type          | Supported Formats                    |
| ------------- | ------------------------------------ |
| Context files | `json`, `yaml`, `yml`, `txt`, `docx` |
| Script files  | `csv`, `xlsx`, `xls`, `txt`, `json`  |

The recommended script format is **CSV with a `scene_hint` column**, because it enables automatic scene-based chunking and better rolling memory.

---

## Example Context YAML

```yaml
project:
  title: "Echoes of the Forest"
  genre: Fantasy RPG
  target_tone: Natural English game dialogue, emotional but not overly dramatic.

first_environment:
  name: "Riverside Village"
  description: "A small, peaceful village surrounded by dense forest."
  lighting: "Bright daylight, late afternoon"
  atmosphere: "Calm and welcoming"

characters:
  - name: Kazuki
    role: protagonist
    personality: "Curious, kind-hearted, slightly impulsive"
    speech_style: "Youthful, natural, emotionally direct"

  - name: Yuki
    role: childhood_friend
    personality: "Calm, observant, protective"
    speech_style: "Soft but practical"

relationships:
  - character_1: Kazuki
    character_2: Yuki
    relationship: "Childhood friends"
    dynamic: "Teasing but caring"

glossary:
  - ja: "結界"
    en: "barrier"
    notes: "Magical barrier. Keep as 'barrier' throughout."

  - ja: "精霊"
    en: "spirit"
    notes: "Nature spirit. Do not translate as 'ghost' or 'soul'."

style_rules:
  - rule: "Kazuki uses contractions such as don't and can't to sound youthful."
  - rule: "Do not localize proper names."
  - rule: "Keep fantasy terms consistent with the glossary."
  - rule: "Use natural English, not stiff literal translation."
```

---

## Example Script CSV

```csv
line_id,character,source_text_ja,scene_hint
1,Kazuki,やっと着いた！ここが噂の村か。,village
2,Yuki,そうだよ。思ったより静かだね。,village
3,Kazuki,精霊の祠って、どこにあるんだろう？,village
4,Yuki,ここだ。結界が張ってある…気をつけて。,temple
5,Kazuki,すごい…この奥の院まで来たのは初めてだ。,temple
6,Sage Takeno,よく来たな。待っておったぞ。,temple
```

---

## Script Columns

| Column           | Meaning                                            |
| ---------------- | -------------------------------------------------- |
| `line_id`        | Unique ID for each script line                     |
| `character`      | Speaker name                                       |
| `source_text_ja` | Japanese source text                               |
| `scene_hint`     | Scene, location, quest, or event used for chunking |

Example chunking:

```text
village → Chunk 1
temple → Chunk 2
forest_path → Chunk 3
boss_room → Chunk 4
```

---

## System Architecture

```text
┌──────────────┐
│    User      │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Next.js UI  │
│  Frontend    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   FastAPI    │
│   Backend    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ File Parser  │
│ Normalizer   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   SQLite     │
│  Database    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Scene Chunker│
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Prompt Builder│
└──────┬───────┘
       │
       ▼
┌──────────────────────────┐
│ OpenAI-Compatible LLM    │
│ OpenAI / Groq / Others   │
└──────┬───────────────────┘
       │
       ▼
┌──────────────┐
│ Translation  │
│ + Memory     │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Review &     │
│ Export       │
└──────────────┘
```

---

## Data Flow

1. Uploaded files go through **parsers** and **normalizers**
2. Normalized context and script lines are stored in SQLite
3. Script lines are grouped by `scene_hint`
4. Each chunk is passed to the prompt builder
5. The LLM returns localized translations and memory
6. Translations are stored in the database
7. Rolling memory is passed to the next chunk
8. The user reviews and edits output
9. Final output is exported as CSV or JSON

---

## Tech Stack

| Layer                       | Technology                            |
| --------------------------- | ------------------------------------- |
| Backend framework           | FastAPI                               |
| Backend language            | Python                                |
| Database                    | SQLite                                |
| ORM                         | SQLAlchemy                            |
| Request/response validation | Pydantic                              |
| Frontend framework          | Next.js                               |
| Frontend language           | TypeScript                            |
| Styling                     | Tailwind CSS                          |
| AI client                   | OpenAI-compatible Python SDK          |
| LLM providers               | OpenAI, Groq, or compatible APIs      |
| File parsing                | pandas, openpyxl, PyYAML, python-docx |

---

## Core Workflow

1. **Upload context**
   Upload game world, characters, glossary, relationships, and style rules.

2. **Upload script**
   Upload Japanese dialogue lines in CSV, XLSX, TXT, or JSON format.

3. **Create chunks**
   The backend groups lines by scene using `scene_hint`.

4. **Translate**
   Each chunk is localized with game context and previous memory.

5. **Generate memory**
   The system creates a memory summary after each chunk.

6. **Review**
   The frontend allows reviewing and editing translations.

7. **Export**
   Export final localized output as CSV or JSON.

---

## API Endpoints

| Method  | Path                               | Description                                  |
| ------- | ---------------------------------- | -------------------------------------------- |
| `GET`   | `/health`                          | Health check                                 |
| `POST`  | `/projects`                        | Create a new project                         |
| `GET`   | `/projects`                        | List all projects                            |
| `GET`   | `/projects/{id}`                   | Get a single project                         |
| `GET`   | `/projects/{id}/context`           | Get context for a project                    |
| `POST`  | `/upload/context`                  | Upload context file and create project       |
| `POST`  | `/upload/script/{project_id}`      | Upload script file                           |
| `POST`  | `/chunks/create/{project_id}`      | Group lines into scene chunks                |
| `GET`   | `/chunks/{project_id}`             | List chunks for a project                    |
| `GET`   | `/chunks/detail/{chunk_id}`        | Get chunk detail with lines and translations |
| `POST`  | `/translate/chunk/{chunk_id}`      | Translate a chunk via AI                     |
| `GET`   | `/translate/{chunk_id}`            | List translations for a chunk                |
| `PATCH` | `/translate/{translation_id}`      | Edit a translation                           |
| `GET`   | `/export/{project_id}?format=csv`  | Export as CSV                                |
| `GET`   | `/export/{project_id}?format=json` | Export as JSON                               |

---

## Project Structure

```text
jp-game-localizer-mvp/
├── README.md
├── backend/
│   ├── .env.example
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── ai/
│   │   │   ├── llm_client.py
│   │   │   └── prompts.py
│   │   ├── routes/
│   │   │   ├── upload.py
│   │   │   ├── chunks.py
│   │   │   ├── translate.py
│   │   │   └── export.py
│   │   └── services/
│   │       ├── file_detector.py
│   │       ├── script_parser.py
│   │       ├── context_parser.py
│   │       ├── normalizer.py
│   │       ├── chunker.py
│   │       ├── memory_service.py
│   │       └── export_service.py
│   └── demo/
│       ├── context.yaml
│       ├── script.csv
│       └── run_demo.md
│
└── frontend/
    ├── app/
    │   ├── layout.tsx
    │   ├── page.tsx
    │   ├── progress/
    │   ├── review/
    │   └── export/
    ├── components/
    ├── lib/
    ├── types/
    └── package.json
```

---

## Backend Setup

```bash
cd backend

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
```

Edit `backend/.env`:

```env
DATABASE_URL=sqlite:///./localizer.db
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.groq.com/openai/v1
OPENAI_MODEL=llama-3.1-8b-instant
DEBUG=true
```

Start the backend:

```bash
uvicorn app.main:app --reload
```

Backend runs at:

```text
http://localhost:8000
```

API docs:

```text
http://localhost:8000/docs
```

---

## Frontend Setup

```bash
cd frontend

npm install
```

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Start the frontend:

```bash
npm run dev
```

Frontend runs at:

```text
http://localhost:3000
```

---

## Demo Workflow

Demo files are available in:

```text
backend/demo/
```

Start backend:

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

Start frontend in another terminal:

```bash
cd frontend
npm run dev
```

Open:

```text
http://localhost:3000
```

Then follow:

```text
Upload Context → Upload Script → Create Chunks → Translate → Review → Export
```

Recommended demo files:

```text
backend/demo/context.yaml
backend/demo/script.csv
```

---

## curl Demo

Upload context:

```bash
curl -X POST http://localhost:8000/upload/context \
  -F "file=@backend/demo/context.yaml;type=text/yaml"
```

Upload script:

```bash
curl -X POST http://localhost:8000/upload/script/1 \
  -F "file=@backend/demo/script.csv;type=text/csv"
```

Create chunks:

```bash
curl -X POST http://localhost:8000/chunks/create/1
```

List chunks:

```bash
curl -s http://localhost:8000/chunks/1 | python -m json.tool
```

Translate a chunk:

```bash
curl -s -X POST http://localhost:8000/translate/chunk/<chunk_id> | python -m json.tool
```

Export CSV:

```bash
curl -s "http://localhost:8000/export/1?format=csv" -o output.csv
```

Export JSON:

```bash
curl -s "http://localhost:8000/export/1?format=json" | python -m json.tool
```

---

## Example Export Output

```json
[
  {
    "line_id": "1",
    "character": "Kazuki",
    "source_text_ja": "やっと着いた！ここが噂の村か。",
    "localized_text_en": "We finally made it! So this is the famous village.",
    "final_text_en": "We finally made it! So this is the famous village.",
    "chunk_number": 1,
    "chunk_title": "village",
    "status": "draft"
  }
]
```

---

## Privacy Notice

This application stores uploaded scripts, context, translations, and rolling memory locally in SQLite.

Uploaded text content may be sent to the configured AI provider, such as OpenAI, Groq, or another OpenAI-compatible API, for translation. External AI provider data handling depends on the configured provider and that provider's privacy policy.

Do not upload confidential, unreleased, copyrighted, or private game content unless you have permission to process it with the configured AI provider.

API keys are stored locally in:

```text
backend/.env
frontend/.env.local
```

These files must never be committed to version control.

Use `.env.example` files to document required variables without exposing secrets.

---

## MVP Limitations

* No authentication
* Single-user local workflow
* No vector database
* No batch translation queue
* No advanced glossary enforcement
* No automated LQA scoring
* No back-translation quality check
* No Unity or Unreal export format yet
* No TMX or XLIFF export yet
* Translation output still benefits from human review

---

## Future Improvements

* Add authentication for deployed usage
* Add delete-project and data cleanup feature
* Add batch translation queue
* Add glossary enforcement checker
* Add character voice consistency scoring
* Add LQA polish step
* Add back-translation quality check
* Add TMX and XLIFF export
* Add Unity localization CSV export
* Add Unreal localization export
* Add local model support for privacy-focused workflows
* Add automated backend and frontend tests
* Add deployment configuration
* Add screenshots and demo video

---

## Technical Terms

### Localization

Localization means adapting content for another language and audience while preserving meaning, tone, context, and cultural readability.

### LLM

LLM stands for Large Language Model. It is an AI model that understands and generates text.

### Context-Aware Translation

Context-aware translation uses extra information such as characters, world details, glossary terms, and tone instead of translating isolated lines.

### Scene-Based Chunking

Scene-based chunking means grouping script lines by scene, location, quest, or event before translation.

### Rolling Memory

Rolling memory is a structured summary from a translated chunk that is passed to the next chunk to maintain continuity.

### Glossary

A glossary is a list of approved translations for important terms, names, items, places, powers, and lore words.

### Human-in-the-Loop

Human-in-the-loop means the AI generates a draft, but a human can review, edit, and approve the final output.

### FastAPI

FastAPI is a Python framework for building backend APIs.

### SQLite

SQLite is a lightweight local database used to store projects, source lines, translations, and memory.

### SQLAlchemy

SQLAlchemy is a Python ORM used to interact with relational databases through Python models.

### Next.js

Next.js is a React framework used to build the frontend interface.

### TypeScript

TypeScript is JavaScript with static typing, helping reduce frontend errors.

---

## Resume Description

```text
Built a full-stack Japanese-to-English game localization MVP using FastAPI, Next.js, SQLite, and OpenAI-compatible LLM APIs. The system parses multi-format context and script files, groups dialogue into scene-based chunks, localizes each chunk with rolling story memory, supports editable review, and exports final translations as CSV/JSON.
```

---

## Project Status

This project is currently an MVP.

Completed:

* Context upload
* Script upload
* Multi-format parsing
* Scene-based chunking
* AI localization
* Rolling memory
* Memory validation fallback
* Review and edit workflow
* CSV/JSON export
* Frontend interface
* Backend API

Recommended use cases:

* Portfolio project
* AI engineering demonstration
* Game localization workflow prototype
* Japanese-to-English localization research prototype
