# lectorius — data pipeline specification

**version:** 1.6
**status:** draft
**last updated:** february 2026

---

## book pack structure

every processed book produces a self-contained directory:

```
books/{book_id}/
├── manifest.json              # pack metadata + processing info
├── raw_text.txt               # normalized source text
├── book.json                  # book metadata (includes tts_provider, voice_id)
├── chapters.jsonl             # chapter boundaries
├── chunks.jsonl               # atomic text units
├── playback_map.jsonl         # chunk → audio mapping
├── audio/
│   └── chunks/
│       └── {chunk_id}.mp3
├── rag/                       # local reference (embeddings live in supabase pgvector)
│   └── meta.jsonl             # vector_id → chunk mapping
├── memory/
│   └── checkpoints.jsonl      # periodic story summaries
└── reports/
    ├── ingest.json
    ├── chapters.json
    ├── chunks.json
    ├── validation.json
    ├── tts.json
    ├── rag.json
    └── memory.json
```

---

## schemas

### manifest.json

```json
{
  "book_id": "pride-and-prejudice",
  "version": 1,
  "created_at": "2025-06-15T14:32:00Z",
  "updated_at": "2025-06-15T16:45:00Z",
  "pipeline_version": "1.0.0",
  "stages_completed": ["ingest", "chapterize", "chunkify", "validate", "tts", "rag", "memory"],
  "config": {
    "tts_voice_id": "dAlhI9qAHVIjXuVppzhW",
    "tts_model": "eleven_multilingual_v2",
    "chunk_target_chars": 600,
    "chunk_min_chars": 100,
    "chunk_max_chars": 1600,
    "checkpoint_interval_chunks": 50,
    "embedding_model": "text-embedding-3-small"
  },
  "stats": {
    "chapters": 24,
    "chunks": 1847,
    "total_audio_duration_ms": 3542000,
    "total_chars": 485000
  }
}
```

### book.json

```json
{
  "book_id": "pride-and-prejudice",
  "title": "Pride and Prejudice",
  "author": "Jane Austen",
  "language": "en",
  "year": 1813,
  "book_type": "fiction",
  "source": "gutenberg",
  "source_id": "pg1342",
  "status": "available",
  "tts_provider": "elevenlabs",
  "voice_id": "dAlhI9qAHVIjXuVppzhW"
}
```

### chapters.jsonl

one json object per line:

```json
{"book_id": "pride-and-prejudice", "chapter_id": "pride-and-prejudice_ch001", "index": 1, "title": "Chapter 1", "char_start": 0, "char_end": 4531}
{"book_id": "pride-and-prejudice", "chapter_id": "pride-and-prejudice_ch002", "index": 2, "title": "Chapter 2", "char_start": 4532, "char_end": 9204}
```

| field | type | description |
|-------|------|-------------|
| book_id | string | book identifier |
| chapter_id | string | format: `{book_id}_ch{index:03d}` |
| index | int | 1-indexed chapter number |
| title | string | chapter title, normalized whitespace |
| char_start | int | start offset in raw_text.txt (inclusive) |
| char_end | int | end offset in raw_text.txt (exclusive) |

### chunks.jsonl

```json
{"book_id": "pride-and-prejudice", "chapter_id": "pride-and-prejudice_ch001", "chunk_id": "pride-and-prejudice_ch001_000001", "chunk_index": 1, "text": "It is a truth universally acknowledged, that a single man in possession of a good fortune, must be in want of a wife.", "char_start": 0, "char_end": 587}
```

| field | type | description |
|-------|------|-------------|
| book_id | string | book identifier |
| chapter_id | string | parent chapter |
| chunk_id | string | format: `{chapter_id}_{chunk_index:06d}` |
| chunk_index | int | global 1-indexed position across entire book |
| text | string | chunk content, whitespace-normalized |
| char_start | int | start offset in raw_text.txt (inclusive) |
| char_end | int | end offset in raw_text.txt (exclusive) |

**invariant:** `raw_text[char_start:char_end]` must reconstruct the chunk text after whitespace normalization.

### playback_map.jsonl

```json
{"chunk_id": "pride-and-prejudice_ch001_000001", "chapter_id": "pride-and-prejudice_ch001", "chunk_index": 1, "audio_path": "audio/chunks/pride-and-prejudice_ch001_000001.mp3", "duration_ms": 4523, "start_ms": 0, "end_ms": 4523}
```

| field | type | description |
|-------|------|-------------|
| chunk_id | string | references chunks.jsonl |
| chapter_id | string | for quick chapter filtering |
| chunk_index | int | for playhead boundary checks |
| audio_path | string | relative path within book pack |
| duration_ms | int | audio duration |
| start_ms | int | always 0 (per-chunk audio) |
| end_ms | int | same as duration_ms |

### rag/meta.jsonl

```json
{"vector_id": 0, "chunk_id": "pride-and-prejudice_ch001_000001", "chunk_index": 1, "chapter_id": "pride-and-prejudice_ch001"}
```

| field | type | description |
|-------|------|-------------|
| vector_id | int | 0-indexed position (matches line number) |
| chunk_id | string | references chunks.jsonl |
| chunk_index | int | for spoiler filtering at query time |
| chapter_id | string | for chapter-scoped retrieval |

**invariant:** line N in meta.jsonl corresponds to vector_id N. the same data is also stored in the supabase `book_embeddings` table for runtime queries.

### memory/checkpoints.jsonl

```json
{
  "book_id": "pride-and-prejudice",
  "checkpoint_index": 5,
  "until_chunk_index": 250,
  "until_chunk_id": "pride-and-prejudice_ch012_000250",
  "summary": "The Bennet family's quiet life in Hertfordshire is disrupted by the arrival of Mr. Bingley and his friend Mr. Darcy...",
  "entities": {
    "people": [
      {"name": "Elizabeth Bennet", "aliases": ["Lizzy", "Eliza"], "role": "protagonist", "description": "Second Bennet daughter, witty and perceptive", "first_chunk": 1, "last_chunk": 248}
    ],
    "places": [
      {"name": "Longbourn", "description": "The Bennet family estate in Hertfordshire", "first_chunk": 1, "last_chunk": 250}
    ],
    "open_threads": [
      {"id": "thread_001", "description": "Elizabeth's growing prejudice against Darcy", "status": "open", "introduced_chunk": 15, "last_updated_chunk": 230}
    ]
  }
}
```

---

## pipeline stages

### stage 1: ingest

**input:** epub file path
**output:** `raw_text.txt`, `book.json`, `manifest.json`, `reports/ingest.json`

#### process

1. **parse epub:** extract spine documents in reading order, strip HTML tags
2. **extract metadata:** populate book.json from opf metadata. if missing, derive from filename or leave as null
3. **concatenate text:** join all spine documents with `\n\n`
4. **strip boilerplate:**
   - remove everything before `*** START OF THE PROJECT GUTENBERG EBOOK`
   - remove everything after `*** END OF THE PROJECT GUTENBERG EBOOK`
   - if markers not found, log warning and keep full text
5. **detect and remove toc:**
   - scan first 15% of text for "table of contents" / "contents" / "index" headers
   - if found, record range in report and remove
6. **normalize whitespace:**
   - `\r\n` → `\n`
   - strip trailing whitespace from each line
   - collapse 3+ consecutive `\n` → `\n\n`
7. **fix hyphenation:**
   - if line ends with `-` and next line starts lowercase: join without hyphen
8. **fix drop caps:**
   - rejoin separated decorative initial letters with their continuation
   - pattern 1: single uppercase + lowercase continuation (`M\nr. Bennet` → `Mr. Bennet`)
   - pattern 2: single uppercase + uppercase word fragment (`D\nURING` → `DURING`, `M\nR. BENNET` → `MR. BENNET`). uses single-newline match only and validates the continuation looks like a word fragment (second char is uppercase, period, or whitespace) rather than a normal sentence start
9. **remove page artifacts:**
   - lines matching `^\s*\d+\s*$` (standalone arabic page numbers)
   - roman numeral page numbers are NOT stripped here — they survive to chapterize so chapter headings like `I`, `II`, `III` aren't lost
10. **fix punctuation spacing:**
    - remove errant spaces before punctuation (e.g., `a draught , and` → `a draught, and`)
11. **strip title/byline:** remove title and author name from start of text (already captured in book.json)

#### llm-assisted analysis (optional)

when `--llm-assist` is passed, the ingest stage calls claude to analyze the raw text after normalization. this helps catch issues that rule-based heuristics miss across different book formats and editions.

**what it analyzes:**
- **narrative boundaries** — identifies where the actual story begins and ends, skipping front matter (title pages, dedications, illustration lists) and back matter (printer colophons, transcriber notes)
- **junk patterns** — regex patterns for non-narrative artifacts to strip (e.g., illustration captions, repeated headers)
- **chapter heading pattern** — the specific regex for this book's chapter headings, passed downstream to the chapterize stage as a priority pattern
- **anomalies** — structural problems observed (e.g., mixed formatting, unusual chapter numbering)

**how it works:**
1. samples the first ~4000 and last ~3000 characters of the normalized text
2. sends to claude sonnet with a structured JSON prompt (see [llm prompt reference](#llm-ingest-analysis-prompt) below)
3. parses the response into an `LLMAnalysis` model stored in `reports/ingest.json`
4. applies narrative boundary trimming using fuzzy phrase matching — finds the LLM-provided markers in the text allowing whitespace/case differences, then trims front/back matter
5. applies junk pattern stripping — compiles each regex and removes matches
6. the `chapter_heading_pattern` is NOT applied here — it flows downstream to chapterize via the ingest report

**safeguards:**
- a **50% trim ratio** limit prevents catastrophic trimming if the LLM returns an incorrect marker. if a start marker would trim more than 50% from the front, or an end marker is before the 50% point, the trim is skipped with a warning
- **fuzzy phrase matching** handles whitespace/case differences between LLM output and actual text — uses the first 5 words of the phrase joined by `\s+` for flexible matching, with a case-insensitive fallback
- **LLM pattern validation** — chapter patterns that match empty or blank strings (e.g., `^$`) are rejected before use

**cost:** ~$0.01-0.02 per book (one API call, ~3000 tokens in, ~500 out)

**failure handling:** if the LLM call fails (API error, bad JSON, missing key), the pipeline continues without LLM analysis and logs a warning. the `--llm-assist` flag is opt-in and never blocks the pipeline.

#### error handling

| condition | action |
|-----------|--------|
| epub parse fails | fail stage, log error |
| no text extracted | fail stage |
| output < 1000 chars | fail with "suspiciously short" error |
| no gutenberg markers | warn, continue with full text |
| no toc found | info log, continue |
| llm analysis fails | warn, continue without analysis |

---

### stage 2: chapterize

**input:** `raw_text.txt`, `reports/ingest.json` (optional)
**output:** `chapters.jsonl`, `reports/chapters.json`

#### process

1. **load LLM hints:** if `reports/ingest.json` exists and contains a `chapter_heading_pattern`, load it and prepend to the pattern list as highest-priority `llm_detected` pattern (after validation)
2. **build candidate list:** scan text line by line, flag potential chapter headers using patterns (in priority order):
   ```
   llm_detected (from ingest report, if available)
   chapter_numbered:    ^\s*(chapter|ch\.?)\s*(\d+|[ivxlcdm]+)\.?\s*(.*)$
   part_book:           ^\s*(part|book)\s+(\d+|[ivxlcdm]+)\.?\s*(.*)$
   section_markers:     ^\s*(prologue|epilogue|introduction|preface|foreword|afterword|postscript)\s*$
   polish_chapter:      ^\s*(rozdzia[łl])\s+(\d+|[ivxlcdm]+)\.?\s*(.*)$
   roman_numeral_line:  ^\s*[IVXLCDM]{1,8}\s*$
   numbered_title:      ^\s*\d{1,3}\.\s+[A-Z]
   all_caps_header:     ^[A-Z][A-Z\s\-\']{5,50}$
   ```
3. **position validation:** candidate must appear at line 0 or after a blank line
4. **drop cap filtering:** single-letter roman numeral matches are checked for drop cap false positives — if the next non-blank line starts with a word fragment (uppercase+uppercase, uppercase+period, or lowercase continuation), it's a drop cap and rejected
5. **context validation:** examine 6 lines following candidate — accept if at least 2 lines look like prose (non-empty, not all-caps, has lowercase)
6. **mid-sentence boundary filtering:** for weak patterns (`roman_numeral_line`, `all_caps_header`, `numbered_title`), check that the text before the boundary ends with sentence punctuation or is a short line (<40 chars). strong patterns (`chapter_numbered`, `llm_detected`, `section_markers`, `part_book`, `polish_chapter`) are always trusted
7. **implicit first chapter:** if the first detected candidate starts more than 500 chars into the text, create an implicit "Chapter 1" covering the text before it (handles front matter or prologues that survive trimming)
8. **build spans:** for each accepted header, set `char_start` / `char_end`
9. **merge tiny chapters:** chapters shorter than 500 chars are merged with the previous chapter
10. **gap detection:** warn if any chapter > 20% of book
11. **fallback:** if zero chapters, create single "Full Text" chapter

#### error handling

| condition | action |
|-----------|--------|
| zero candidates found | warn, create single chapter |
| chapter span < 500 chars | warn, merge with previous |
| overlapping char ranges | fail stage |
| duplicate chapter titles | warn, append index |

---

### stage 3: chunkify

**input:** `raw_text.txt`, `chapters.jsonl`
**output:** `chunks.jsonl`, `reports/chunks.json`

#### configuration

| parameter | default | description |
|-----------|---------|-------------|
| TARGET_CHARS | 600 | ideal chunk size (~30-50 seconds of audio at typical narration speed) |
| MIN_CHARS | 200 | minimum chunk size |
| MAX_CHARS | 1600 | hard maximum |

> **Note:** Each chunk should end with sentence-ending punctuation (`.`, `!`, `?`) to ensure natural audio breaks. The chunker will extend past TARGET_CHARS (up to MAX_CHARS) if needed to reach a sentence boundary.

#### process

1. initialize `global_chunk_index = 0`
2. for each chapter:
   - extract text from raw_text using char offsets
   - **strip chapter heading** from start of chapter text — matches `chapter/ch.` + number, roman numeral lines, or section markers (`prologue`, `epilogue`, etc.). the heading is already captured in chapter metadata and shouldn't appear in chunk text
   - split into paragraphs on `\n\n+`
   - unwrap hard-wrapped lines within paragraphs
   - convert paragraphs to units (sentence-split if > MAX_CHARS)
   - pack units into chunks ≤ MAX_CHARS
   - **merge tiny chunks** < MIN_CHARS with neighbors:
     - backward merge: merge with previous chunk if combined size ≤ MAX_CHARS
     - **forward merge:** if the first chunk in a chapter is still tiny after backward merge, merge it into the next chunk
   - **merge heading-only chunks:** chunks < 50 chars that don't end with sentence punctuation are merged forward into the next chunk
   - emit chunks with incrementing global index

#### sentence splitting

**primary (spacy):**
```python
nlp = spacy.load("en_core_web_sm")
sentences = [sent.text for sent in nlp(paragraph).sents]
```

**fallback (regex):**
```python
pattern = r'(?<=[.!?])\s+(?=[A-Z])'
sentences = re.split(pattern, paragraph)
```

#### error handling

| condition | action |
|-----------|--------|
| chunk > MAX_CHARS after splitting | fail stage |
| empty chapter produces zero chunks | warn, skip chapter |
| offset mismatch | fail stage |
| spacy model not found | warn, use regex fallback |

---

### stage 4: validate

**input:** `chunks.jsonl`
**output:** `reports/validation.json`

#### checks

| check | severity | condition |
|-------|----------|-----------|
| empty text | ERROR | `len(chunk.text.strip()) == 0` |
| too short | WARN | `len(chunk.text) < MIN_CHARS` |
| too long | ERROR | `len(chunk.text) > MAX_CHARS` |
| duplicate chunk_id | ERROR | chunk_id appears more than once |
| duplicate text | WARN | identical text in multiple chunks |
| non-prose | WARN | text is only digits/punctuation/whitespace |
| chunk index gap | ERROR | chunk_index values not sequential |
| offset overlap | ERROR | chunk N's char_end > chunk N+1's char_start |
| offset gap | WARN | missing text between chunks |

#### gate logic

- any ERROR → stage fails, pipeline halts
- WARN only → stage passes, warnings logged

---

### stage 5: generate audio (tts)

**input:** `chunks.jsonl`, `book.json` (optional — for provider/voice defaults)
**output:** `audio/chunks/*.mp3`, `playback_map.jsonl`, `reports/tts.json`

#### provider resolution

the tts stage resolves provider and voice using a priority chain:

```
CLI --provider/--voice flags  →  book.json tts_provider/voice_id  →  "openai" default
```

this means `lectorius-pipeline tts --book-dir ./books/pride-and-prejudice` reads the provider and voice from `book.json` automatically — no flags needed.

#### providers

| provider | model | default voice | use case |
|----------|-------|---------------|----------|
| openai | gpt-4o-mini-tts | nova | development, testing |
| elevenlabs | eleven_multilingual_v2 | (from book.json or `ELEVENLABS_VOICE_ID` env) | production quality |

**openai voices:** alloy, ash, ballad, coral, echo, fable, nova, onyx, sage, shimmer, verse

#### configuration

| parameter | description |
|-----------|-------------|
| provider | `openai` or `elevenlabs` (resolved from book.json if not specified) |
| voice | openai voice name or elevenlabs voice_id (resolved from book.json if not specified) |
| model | openai: `gpt-4o-mini-tts` / elevenlabs: `eleven_multilingual_v2` |
| concurrency | max parallel requests (default: 5) |
| retry_attempts | max retries per chunk (default: 3) |

#### process

1. resolve provider/voice from CLI flags, book.json, or defaults
2. load progress from existing tts.json if resuming
3. for each chunk:
   - skip if already completed
   - call provider api
   - save to `audio/chunks/{chunk_id}.mp3`
   - measure duration via mutagen
   - write playback_map entry
   - update progress
4. retry with exponential backoff on failures (base: 2.0s)
5. sort playback_map.jsonl by chunk_index

#### cli

```bash
# auto-detect provider/voice from book.json
lectorius-pipeline tts --book-dir ./books/pride-and-prejudice

# explicit openai (overrides book.json)
lectorius-pipeline tts --book-dir ./books/my-book --provider openai --voice nova

# explicit elevenlabs
lectorius-pipeline tts --book-dir ./books/my-book --provider elevenlabs --voice <voice_id>

# resume interrupted processing
lectorius-pipeline tts --book-dir ./books/my-book --resume
```

#### resumability

fully resumable—rerun skips completed chunks, processes only missing/failed.

#### error handling

| condition | action |
|-----------|--------|
| api rate limit (429) | backoff and retry |
| api server error (5xx) | backoff and retry |
| api client error (4xx) | log failure, skip chunk |
| audio file write fails | fail stage |

---

### stage 6: build rag index

**input:** `chunks.jsonl`, embedding configuration, supabase credentials
**output:** `rag/meta.jsonl` (local reference), supabase `book_embeddings` table, `reports/rag.json`

#### configuration

| parameter | description |
|-----------|-------------|
| embedding_model | `text-embedding-3-small` (default) |
| embedding_dimensions | 1536 |
| batch_size | chunks per api call (default: 100) |

#### process

1. batch process chunks:
   - embed texts via openai api
   - normalize vectors (L2)
   - write meta.jsonl entries
2. insert embeddings into supabase `book_embeddings` table:
   - delete existing rows for this book_id (idempotent re-runs)
   - insert rows in batches of 100 with book_id, chunk_id, chunk_index, chapter_id, embedding

#### environment variables

requires `OPENAI_API_KEY`, `SUPABASE_URL`, and `SUPABASE_SERVICE_KEY` (service key, not anon — bypasses RLS for insert).

#### outputs

| output | location | purpose |
|--------|----------|---------|
| `rag/meta.jsonl` | local book dir | local reference, maps vector_id to chunk |
| `book_embeddings` rows | supabase postgres | web app vector similarity search via pgvector |

#### runtime query contract (web app)

```sql
-- supabase rpc or postgrest query
select chunk_id, chunk_index, chapter_id,
       1 - (embedding <=> $query_embedding) as similarity
from book_embeddings
where book_id = $book_id
  and chunk_index <= $current_chunk_index  -- no spoilers
order by embedding <=> $query_embedding
limit $k;
```

---

### stage 7: generate memory checkpoints

**input:** `chunks.jsonl`, llm configuration
**output:** `memory/checkpoints.jsonl`, `reports/memory.json`

#### configuration

| parameter | description |
|-----------|-------------|
| checkpoint_interval | chunks between checkpoints (default: 50) |
| llm_model | e.g., `claude-sonnet-4-20250514` |
| max_context_chunks | max chunks to include in llm call (default: 60) |

#### process

1. determine checkpoint positions:
   - **short books** (< 100 chunks): checkpoints at 25%, 50%, 75%, and 100%
   - **longer books**: every N chunks (default: 50) + final position
2. for each position:
   - gather previous checkpoint + new chunks
   - build prompt requesting json output
   - call llm (max_tokens: 8192), parse response
   - write checkpoint

#### llm prompt

```
You are summarizing a book for a reading assistant. Update the running summary and entity tracking based on new content.

PREVIOUS STATE:
{previous_checkpoint_json or "This is the first checkpoint."}

NEW CONTENT (chunks {start} to {end}):
{chunk_texts}

Output valid JSON:
{
  "summary": "...",
  "entities": {
    "people": [{"name": "...", "aliases": [...], "role": "...", "description": "...", "first_chunk": N, "last_chunk": N}],
    "places": [{"name": "...", "description": "...", "first_chunk": N, "last_chunk": N}],
    "open_threads": [{"id": "...", "description": "...", "status": "open|resolved", "introduced_chunk": N, "last_updated_chunk": N}]
  }
}
```

#### runtime query contract

```python
def get_memory_context(current_chunk_index: int) -> dict:
    for checkpoint in reversed(checkpoints):
        if checkpoint["until_chunk_index"] <= current_chunk_index:
            return checkpoint
    return None
```

#### future optimizations (todo)

##### entity pruning for long books

**issue:** memory checkpoints carry forward ALL entities cumulatively. for complex novels like pride & prejudice (30+ characters, 20+ threads), later checkpoints can exceed token limits.

**current state:** max_tokens set to 8192, which handles MVP books but may not scale to epic novels (war and peace, les misérables).

**proposed fix for v2:**

1. **prune inactive entities** — only include characters/places seen in last 200 chunks
2. **cap entity lists** — top 15-20 characters by importance (protagonist/antagonist/supporting only, drop "mentioned")
3. **drop resolved threads** — remove threads marked "resolved" from previous checkpoints
4. **compress descriptions** — limit entity descriptions to 50 chars

**implementation sketch:**
```python
def prune_entities(entities: Entities, current_chunk: int, lookback: int = 200) -> Entities:
    cutoff = current_chunk - lookback

    # Keep only recently active characters
    active_people = [p for p in entities.people if p.last_chunk >= cutoff or p.role in ("protagonist", "antagonist")]

    # Cap at top 20
    active_people = sorted(active_people, key=lambda p: p.last_chunk, reverse=True)[:20]

    # Drop resolved threads
    open_threads = [t for t in entities.open_threads if t.status == "open"]

    return Entities(people=active_people, places=entities.places, open_threads=open_threads)
```

**trigger:** implement when processing books with 1000+ chunks or if memory stage costs exceed $5/book.

---

### stage 8: generate fallback audio

**input:** `book.json` (for voice/provider) OR explicit `--provider`/`--voice` flags
**output:** per-voice fallback MP3s uploaded to supabase storage

this is a standalone stage (not part of the `process` pipeline) that generates pre-recorded error/fallback audio in the book's narrator voice, so the web app can serve instant responses that match the book's voice instead of a generic fallback.

#### fallback phrases

| id | text | use case |
|----|------|----------|
| `no_context_yet` | "I don't have enough context yet. Let's keep reading." | question asked before chunk 5 |
| `error` | "I can't seem to find an answer right now." | api/tts failure during Q&A |
| `book_only` | "I can only help with questions about this book." | off-topic question |

#### resolution

provider and voice are resolved using the same priority chain as the TTS stage:

```
CLI --provider/--voice flags  →  book.json tts_provider/voice_id  →  error (no default)
```

unlike the TTS stage, there is no default provider — at least one source of provider/voice is required.

#### process

1. resolve provider and voice from flags or book.json
2. create supabase storage client
3. for each fallback phrase:
   - check if `system/fallback-audio/{voice_id}/{id}.mp3` already exists in storage
   - if not, generate audio via TTS provider
   - upload to supabase storage
4. return status for each fallback (uploaded or already existed)

#### storage structure

```
supabase storage / system /
├── audio/                          ← generic fallbacks (OpenAI "alloy")
│   ├── no_context_yet.mp3
│   ├── error.mp3
│   └── book_only.mp3
└── fallback-audio/                 ← per-voice fallbacks
    ├── dAlhI9qAHVIjXuVppzhW/      ← pride-and-prejudice voice
    │   ├── no_context_yet.mp3
    │   ├── error.mp3
    │   └── book_only.mp3
    └── .../
```

books sharing the same `voice_id` share fallback files. generic fallbacks remain as final fallback when no per-voice version exists.

#### environment variables

requires `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` for storage access, plus the relevant TTS provider key (`OPENAI_API_KEY` or `ELEVENLABS_API_KEY`).

#### cli

```bash
# from book.json (reads provider + voice automatically)
lectorius-pipeline generate-fallbacks --book-dir ./books/pride-and-prejudice

# explicit provider + voice (no book-dir needed)
lectorius-pipeline generate-fallbacks --provider elevenlabs --voice dAlhI9qAHVIjXuVppzhW

# with verbose logging
lectorius-pipeline generate-fallbacks --book-dir ./books/pride-and-prejudice -v
```

---

## pipeline orchestration

### cli interface

```bash
# full pipeline (ingest through validate)
lectorius-pipeline process --input book.epub --book-id pride-and-prejudice \
  --output-dir ./books/pride-and-prejudice

# with llm-assisted text analysis
lectorius-pipeline process --input book.epub --book-id pride-and-prejudice \
  --output-dir ./books/pride-and-prejudice --llm-assist

# set tts provider/voice in book.json during ingest
lectorius-pipeline process --input book.epub --book-id pride-and-prejudice \
  --output-dir ./books/pride-and-prejudice --tts-provider elevenlabs --voice-id <id>

# stop after a specific stage
lectorius-pipeline process --input book.epub --book-id pride-and-prejudice \
  --output-dir ./books/pride-and-prejudice --stop-after chunkify

# resume from a specific stage
lectorius-pipeline process --input book.epub --book-id pride-and-prejudice \
  --output-dir ./books/pride-and-prejudice --from-stage chapterize

# individual stages (text processing)
lectorius-pipeline ingest --input book.epub --book-id pride-and-prejudice \
  --output-dir ./books/pride-and-prejudice
lectorius-pipeline ingest --input book.epub --book-id pride-and-prejudice \
  --output-dir ./books/pride-and-prejudice --llm-assist
lectorius-pipeline chapterize --book-dir ./books/pride-and-prejudice --book-id pride-and-prejudice
lectorius-pipeline chunkify --book-dir ./books/pride-and-prejudice --book-id pride-and-prejudice
lectorius-pipeline validate --book-dir ./books/pride-and-prejudice --book-id pride-and-prejudice

# audio generation (reads provider/voice from book.json)
lectorius-pipeline tts --book-dir ./books/pride-and-prejudice
lectorius-pipeline tts --book-dir ./books/pride-and-prejudice --resume

# rag index
lectorius-pipeline rag --book-dir ./books/pride-and-prejudice

# memory checkpoints
lectorius-pipeline memory --book-dir ./books/pride-and-prejudice

# per-voice fallback audio
lectorius-pipeline generate-fallbacks --book-dir ./books/pride-and-prejudice

# verbose logging (works with any command)
lectorius-pipeline process --input book.epub --book-id pride-and-prejudice \
  --output-dir ./books/pride-and-prejudice -v
```

### stage dependencies

```
ingest → chapterize → chunkify → validate → tts → [rag, memory]
                                              ↘      ↗
                                           (parallel)

generate-fallbacks  (standalone, requires book.json or explicit flags)
```

### manifest updates

after each stage:
- add stage name to `stages_completed`
- update `updated_at`
- update relevant `stats` fields

### failure recovery

- `stages_completed` shows last successful stage
- rerun with `--from-stage {next}` to resume
- tts has internal resumability

---

## configuration file

`lectorius.config.yaml`:

```yaml
pipeline:
  version: "1.0.0"

chunking:
  target_chars: 600
  min_chars: 200
  max_chars: 1600
  sentence_splitter: regex       # "regex" (default) or "spacy"
  spacy_model_en: en_core_web_sm # used when sentence_splitter is "spacy"

tts:
  # provider and voice are typically set per-book in book.json
  # these serve as defaults when book.json doesn't specify
  provider: openai               # "openai" or "elevenlabs"
  openai_model: gpt-4o-mini-tts
  openai_voice: nova
  elevenlabs_model: eleven_multilingual_v2
  elevenlabs_voice_id: ${ELEVENLABS_VOICE_ID}
  output_format: mp3_44100_128
  concurrency: 5
  retry_attempts: 3
  retry_backoff_base: 2

rag:
  embedding_provider: openai
  embedding_model: text-embedding-3-small
  embedding_dimensions: 1536
  batch_size: 100
  # embeddings are inserted into supabase book_embeddings table
  # requires SUPABASE_URL and SUPABASE_SERVICE_KEY env vars

memory:
  checkpoint_interval: 50
  llm_provider: anthropic
  llm_model: claude-sonnet-4-20250514
  max_context_chunks: 60

paths:
  books_dir: ./books
  temp_dir: ./tmp
  logs_dir: ./logs
```

---

## llm ingest analysis prompt

the prompt sent to claude during `--llm-assist` ingest. it receives the first ~4000 and last ~3000 characters of the normalized text:

```
You are analyzing the raw text extracted from a digitized book for an audiobook pipeline.
The text has already had Gutenberg boilerplate removed, but may still contain:
- Front matter (title pages, dedication, epigraphs, illustration lists, publisher info)
- Back matter (printer colophons, transcriber notes, advertisement pages)
- Illustration captions or artifacts (e.g., "See larger view", "[Illustration: ...]")
- Drop cap artifacts (single capital letters on their own line at chapter starts)

Book title: {title}
Book author: {author}
Total text length: {total_chars} characters

FIRST {head_len} CHARACTERS:
"""
{head_sample}
"""

LAST {tail_len} CHARACTERS:
"""
{tail_sample}
"""

Analyze the text and return ONLY valid JSON (no markdown, no explanation) with this schema:
{
  "narrative_start_marker": "<exact line where story prose begins>",
  "narrative_end_marker": "<exact line where story prose ends>",
  "junk_patterns": ["<Python regex patterns for non-narrative artifacts>"],
  "chapter_heading_pattern": "<Python regex matching chapter headings>",
  "chapter_heading_examples": ["<2-3 example headings>"],
  "anomalies": ["<structural problems observed>"]
}
```

the response is parsed into an `LLMAnalysis` pydantic model:

```python
class LLMAnalysis(BaseModel):
    narrative_start_marker: str = ""
    narrative_end_marker: str = ""
    junk_patterns: list[str] = Field(default_factory=list)
    chapter_heading_pattern: str = ""
    chapter_heading_examples: list[str] = Field(default_factory=list)
    anomalies: list[str] = Field(default_factory=list)
    model_used: str = ""
    tokens_used: int = 0
```

**data flow:** the `chapter_heading_pattern` from the LLM flows to the chapterize stage via `reports/ingest.json`. the chapterize runner loads the report and prepends the pattern to its detection list as the highest-priority `llm_detected` pattern. this allows the LLM to teach the pipeline about book-specific heading formats that the built-in patterns don't cover.

---

## environment variables

| variable | required by | description |
|----------|-------------|-------------|
| `OPENAI_API_KEY` | tts (openai), rag | openai api key for TTS and embeddings |
| `ELEVENLABS_API_KEY` | tts (elevenlabs), generate-fallbacks | elevenlabs api key |
| `ELEVENLABS_VOICE_ID` | tts (elevenlabs) | fallback voice id if not in book.json or CLI |
| `ANTHROPIC_API_KEY` | ingest (--llm-assist), memory | anthropic api key for claude |
| `SUPABASE_URL` | rag, generate-fallbacks | supabase project url |
| `SUPABASE_SERVICE_KEY` | rag, generate-fallbacks | supabase service key (not anon — bypasses RLS) |

---

## appendix: regex patterns

### chapter detection (in priority order)

```python
CHAPTER_PATTERNS = [
    # llm_detected: prepended dynamically from ingest report
    r'^\s*(chapter|ch\.?)\s*(\d+|[ivxlcdm]+)\.?\s*(.*)$',     # chapter_numbered
    r'^\s*(part|book)\s+(\d+|[ivxlcdm]+)\.?\s*(.*)$',          # part_book
    r'^\s*(prologue|epilogue|introduction|preface|foreword|afterword|postscript)\s*$',
    r'^\s*(rozdzia[łl])\s+(\d+|[ivxlcdm]+)\.?\s*(.*)$',        # polish_chapter
    r'^\s*[IVXLCDM]{1,8}\s*$',                                  # roman_numeral_line
    r'^\s*\d{1,3}\.\s+[A-Z]',                                   # numbered_title
    r'^[A-Z][A-Z\s\-\']{5,50}$',                                # all_caps_header
]
```

note: `chapter_numbered` uses `\s*` (zero or more spaces) between the word "chapter" and the numeral. this handles malformed gutenberg texts where the space is missing (e.g., `CHAPTERXXVII.`).

### drop cap detection

```python
# normalizer: rejoin drop caps during ingest
r'^([A-Z])\n{1,2}([a-z])'            # pattern 1: M + r. Bennet → Mr. Bennet
r'^([A-Z])\n([A-Z])(?=[A-Z.\s])'     # pattern 2: D + URING → DURING

# detector: filter surviving drop caps during chapterize
# single-letter line where next non-blank line:
#   - starts lowercase (clearly a drop cap), OR
#   - second char is uppercase/period (word fragment like R., URING)
```

### sentence splitting (fallback)

```python
SENTENCE_END = r'(?<=[.!?])(?<![A-Z]\.)(?<!Mr\.)(?<!Mrs\.)(?<!Dr\.)\s+(?=[A-Z"])'
```

### page artifacts

```python
PAGE_NUMBER = r'^\s*\d{1,4}\s*$'
```
