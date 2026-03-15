# lectorius

an interactive audiobook platform with ai-powered, spoiler-free q&a

![sveltekit](https://img.shields.io/badge/sveltekit-ff3e00?style=flat&logo=svelte&logoColor=white)
![typescript](https://img.shields.io/badge/typescript-3178c6?style=flat&logo=typescript&logoColor=white)
![python](https://img.shields.io/badge/python-3776ab?style=flat&logo=python&logoColor=white)
![tailwind](https://img.shields.io/badge/tailwind-06b6d4?style=flat&logo=tailwindcss&logoColor=white)
![supabase](https://img.shields.io/badge/supabase-3fcf8e?style=flat&logo=supabase&logoColor=white)
![anthropic](https://img.shields.io/badge/anthropic-d4a574?style=flat&logo=anthropic&logoColor=white)
![openai](https://img.shields.io/badge/openai-412991?style=flat&logo=openai&logoColor=white)
![elevenlabs](https://img.shields.io/badge/elevenlabs-000000?style=flat)

---

## demo

**[lectorius.vercel.app](https://lectorius.vercel.app)**

---

## what it does

- **push-to-talk q&a** — hold a button to ask a question while listening. the system transcribes your speech, queries claude with spoiler-filtered context, and streams the answer back sentence-by-sentence as speech in the narrator's own voice — all within ~3 seconds
- **spoiler prevention** — rag retrieval and memory checkpoints are hard-filtered to the listener's current position. the llm never sees text beyond the playhead
- **multi-provider tts pipeline** — a 7-stage python pipeline converts epub files into full audiobook packs with per-book voice assignment (openai or elevenlabs), vector embeddings (pgvector), and running story summaries via claude
- **ambient music** — book-themed background playlists with volume ducking during q&a

---

## architecture

```
┌─────────────────────────────────────────────────────────┐
│                     pipeline (python)                   │
│                                                         │
│  epub → ingest → chapterize → chunkify → validate       │
│                                             │           │
│                                    ┌────────┼────────┐  │
│                                    ▼        ▼        ▼  │
│                                   tts      rag    memory│
│                                    │        │        │  │
│                                    ▼        ▼        ▼  │
│                                  mp3s   pgvector  json  │
│                                    │        │        │  │
│                                    └────────┼────────┘  │
│                                             ▼           │
│                                     supabase storage    │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                    web app (sveltekit)                  │
│                                                         │
│  browser                          vercel api routes     │
│  ┌───────────────┐                ┌──────────────────┐  │
│  │ audio player  │  POST /ask     │ whisper (stt)    │  │
│  │ music player  │ ──────────────►│ claude (llm)     │  │
│  │ push-to-talk  │ ◄──────────────│ tts (streaming)  │  │
│  │ library + ui  │   SSE stream   │ pgvector (rag)   │  │
│  └───────────────┘                └──────────────────┘  │
│        │                                  │             │
│        ▼                                  ▼             │
│   localstorage                    supabase + redis      │
└─────────────────────────────────────────────────────────┘
```

**pipeline** processes epub files through 7 stages: text extraction and normalization, chapter detection (with optional but recommended llm-assisted analysis), sentence-aware chunking, validation, multi-provider tts audio generation, pgvector embedding indexing, and claude-powered memory checkpoints. outputs self-contained book packs uploaded to supabase.

**web app** serves the audiobook player. when a user asks a question, the server transcribes speech via whisper, assembles spoiler-filtered context (recent text + memory checkpoint + rag results), streams claude's response sentence-by-sentence, converts each sentence to speech via the book's tts provider, and pushes base64 audio back to the client as sse events. first audio plays while remaining sentences are still generating.

---

## tech highlights

- **streaming claude → sentence-by-sentence tts** — llm tokens are buffered into sentences as they arrive. each completed sentence is immediately tts'd and pushed to the client via sse. the user hears the first sentence ~6s after asking, while the rest of the answer is still being generated and spoken

- **pgvector rag with spoiler-aware filtering** — chunk embeddings are stored in supabase postgres with pgvector. at query time, similarity search is filtered to `chunk_index <= current_position`, ensuring the llm never retrieves text the listener hasn't heard yet

- **per-book voice assignment** — each book has its own tts provider (openai or elevenlabs) and voice configured in `book.json`. the q&a assistant responds in the same voice as the narrator. pre-recorded per-voice fallback audio ensures even error messages match the narrator

- **3-phase recorder warm-up** — mic stream acquired on first play (browser gesture requirement), `MediaRecorder` pre-initialized on button hover, instant start on press. eliminates ~1.5s of recording latency

- **access control + rate limiting** — 3-question free tier per ip, access codes for unlimited use, upstash redis sliding window (60/hr). hooks middleware with graceful degradation — redis failures don't block users

- **ambient music with ducking** — background playlists from supabase storage. music volume fades to zero during q&a recording/answering, unducks on resume. optional sync-with-book-playback toggle

---

## getting started

### prerequisites

- node.js 18+
- python 3.11+
- api keys: openai, anthropic, elevenlabs (optional), supabase project, upstash redis (optional)

### setup

```bash
git clone https://github.com/jan-barg/lectorius.git
cd lectorius

# install web app dependencies
npm install

# install pipeline
cd pipeline
python -m venv .venv
source .venv/bin/activate
pip install -e .
cd ..
```

### environment variables

create `apps/web/.env`:

```bash
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=xxx
OPENAI_API_KEY=xxx
ANTHROPIC_API_KEY=xxx
ELEVENLABS_API_KEY=xxx              # optional — only for elevenlabs books
UPSTASH_REDIS_REST_URL=xxx          # optional — rate limiting disabled without
UPSTASH_REDIS_REST_TOKEN=xxx
```

pipeline uses env vars directly: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `ELEVENLABS_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`.

### run the pipeline

```bash
cd pipeline && source .venv/bin/activate

# process a book (stages 1-4: text processing)
lectorius-pipeline process \
  --input ../source/pride-and-prejudice.epub \
  --book-id pride-and-prejudice \
  --output-dir ../books/pride-and-prejudice \
  --llm-assist

# generate audio (stage 5)
lectorius-pipeline tts --book-dir ../books/pride-and-prejudice

# build rag index (stage 6) + memory checkpoints (stage 7)
lectorius-pipeline rag --book-dir ../books/pride-and-prejudice
lectorius-pipeline memory --book-dir ../books/pride-and-prejudice

# generate per-voice fallback audio
lectorius-pipeline generate-fallbacks --book-dir ../books/pride-and-prejudice
```

upload the book pack to supabase storage, then:

### run the web app

```bash
npm run dev
```

---

## project structure

```
lectorius/
├── apps/web/                    # sveltekit web application
│   └── src/
│       ├── routes/api/          # server endpoints (books, ask, verify-code, music)
│       ├── lib/server/          # server modules (clients, context, rag, tts, prompts)
│       ├── lib/components/      # svelte components (player, qa, library, settings, music)
│       ├── lib/services/        # audio engine, music engine, recorder
│       └── lib/stores/          # playback, qa, book, music, settings state
├── pipeline/                    # python data pipeline
│   └── src/lectorius_pipeline/
│       ├── stages/              # ingest, chapterize, chunkify, validate, tts, rag, memory, fallbacks
│       ├── schemas.py           # pydantic models
│       └── cli.py               # click cli
├── docs/                        # detailed specifications
│   ├── prd.md                   # product requirements
│   ├── architecture.md          # system architecture
│   ├── pipeline.md              # pipeline specification
│   ├── api-spec.md              # api specification
│   ├── data-model.md            # data model
│   ├── playback-state-machine.md # playback state machine
│   └── llm-prompts.md           # llm prompt specification
├── source/                      # source epub files
└── books/                       # pipeline output (audio gitignored)
```

---

## cost breakdown

### monthly infrastructure

| service | cost |
|---------|------|
| supabase (pro) | $25/mo |
| vercel (hobby) | free |
| upstash redis (free tier) | free |

### per-question cost (~$0.02-0.03)

| service | cost |
|---------|------|
| whisper transcription (~5s audio) | ~$0.001 |
| claude sonnet (~2k in, 500 out tokens) | ~$0.01 |
| elevenlabs tts (~100 words) | ~$0.01-0.02 |

### per-book pipeline cost

| service | cost |
|---------|------|
| tts (full audiobook, elevenlabs) | ~$5-$150 depending on length |
| embeddings (text-embedding-3-small) | ~$0.01 |
| memory checkpoints (claude) | ~$0.50-$5.00 |
| llm-assisted ingest (claude) | ~$0.10 |

---

## docs

detailed specifications for every component:

- [product requirements](docs/prd.md)
- [system architecture](docs/architecture.md)
- [data pipeline](docs/pipeline.md)
- [api specification](docs/api-spec.md)
- [data model](docs/data-model.md)
- [playback state machine](docs/playback-state-machine.md)
- [llm prompts](docs/llm-prompts.md)
- [pipeline readme](pipeline/README.md)

---

## license

mit
