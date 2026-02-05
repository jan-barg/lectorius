# lectorius — data pipeline specification

**version:** 1.1  
**status:** draft  
**last updated:** february 2026

---

## book pack structure

every processed book produces a self-contained directory:

```
books/{book_id}/
├── manifest.json              # pack metadata + processing info
├── raw_text.txt               # normalized source text
├── book.json                  # book metadata
├── chapters.jsonl             # chapter boundaries
├── chunks.jsonl               # atomic text units
├── playback_map.jsonl         # chunk → audio mapping
├── audio/
│   └── chunks/
│       └── {chunk_id}.mp3
├── rag/
│   ├── index.faiss            # vector index
│   └── meta.jsonl             # chunk metadata for retrieval
├── memory/
│   └── checkpoints.jsonl      # periodic story summaries
└── reports/
    ├── ingest.json
    ├── chapters.json
    ├── chunks.json
    └── tts.json
```

---

## schemas

### manifest.json

```json
{
  "book_id": "b001",
  "version": 1,
  "created_at": "2025-06-15T14:32:00Z",
  "updated_at": "2025-06-15T16:45:00Z",
  "pipeline_version": "1.0.0",
  "stages_completed": ["ingest", "chapterize", "chunkify", "validate", "tts", "rag", "memory"],
  "config": {
    "tts_voice_id": "voice_abc123",
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
  "book_id": "b001",
  "title": "Pan Tadeusz",
  "author": "Adam Mickiewicz",
  "language": "pl",
  "year": 1834,
  "book_type": "fiction",
  "source": "gutenberg",
  "source_id": "pg12345"
}
```

### chapters.jsonl

one json object per line:

```json
{"book_id": "b001", "chapter_id": "b001_ch001", "index": 1, "title": "Księga pierwsza: Gospodarstwo", "char_start": 0, "char_end": 24531}
{"book_id": "b001", "chapter_id": "b001_ch002", "index": 2, "title": "Księga druga: Zamek", "char_start": 24532, "char_end": 51204}
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
{"book_id": "b001", "chapter_id": "b001_ch001", "chunk_id": "b001_ch001_000001", "chunk_index": 1, "text": "Litwo! Ojczyzno moja! ty jesteś jak zdrowie...", "char_start": 0, "char_end": 587}
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
{"chunk_id": "b001_ch001_000001", "chapter_id": "b001_ch001", "chunk_index": 1, "audio_path": "audio/chunks/b001_ch001_000001.mp3", "duration_ms": 4523, "start_ms": 0, "end_ms": 4523}
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
{"vector_id": 0, "chunk_id": "b001_ch001_000001", "chunk_index": 1, "chapter_id": "b001_ch001"}
```

| field | type | description |
|-------|------|-------------|
| vector_id | int | index in faiss (0-indexed, matches line number) |
| chunk_id | string | references chunks.jsonl |
| chunk_index | int | for spoiler filtering at query time |
| chapter_id | string | for chapter-scoped retrieval |

**invariant:** line N in meta.jsonl corresponds to vector N in index.faiss.

### memory/checkpoints.jsonl

```json
{
  "book_id": "b001",
  "checkpoint_index": 5,
  "until_chunk_index": 250,
  "until_chunk_id": "b001_ch003_000250",
  "summary": "The story follows Tadeusz returning to Lithuania...",
  "entities": {
    "people": [
      {"name": "Tadeusz", "aliases": ["Pan Tadeusz"], "role": "protagonist", "description": "Young nobleman returning home", "first_chunk": 1, "last_chunk": 248}
    ],
    "places": [
      {"name": "Soplicowo", "description": "The Soplica family estate", "first_chunk": 1, "last_chunk": 250}
    ],
    "open_threads": [
      {"id": "thread_001", "description": "Castle ownership dispute", "status": "open", "introduced_chunk": 45, "last_updated_chunk": 230}
    ]
  }
}
```

---

## pipeline stages

### stage 1: ingest

**input:** epub file path  
**output:** `raw_text.txt`, `book.json`, `reports/ingest.json`

#### process

1. **parse epub:** extract spine documents in reading order
2. **extract metadata:** populate book.json from opf metadata. if missing, derive from filename or leave as null
3. **concatenate text:** join all spine documents with `\n\n`
4. **strip boilerplate:**
   - remove everything before `*** START OF THE PROJECT GUTENBERG EBOOK`
   - remove everything after `*** END OF THE PROJECT GUTENBERG EBOOK`
   - if markers not found, log warning and keep full text
5. **detect and remove toc:**
   - scan first 15% of text for toc patterns
   - if found, record range in report and remove
6. **normalize whitespace:**
   - `\r\n` → `\n`
   - strip trailing whitespace from each line
   - collapse 3+ consecutive `\n` → `\n\n`
7. **fix hyphenation:**
   - if line ends with `-` and next line starts lowercase: join without hyphen
8. **remove page artifacts:**
   - lines matching `^\s*\d+\s*$` (page numbers)
   - lines matching `^\s*[ivxlcdm]+\s*$` alone (roman numerals)
   - repeated header/footer lines

#### error handling

| condition | action |
|-----------|--------|
| epub parse fails | fail stage, log error |
| no text extracted | fail stage |
| output < 1000 chars | fail with "suspiciously short" error |
| no gutenberg markers | warn, continue with full text |
| no toc found | info log, continue |

---

### stage 2: chapterize

**input:** `raw_text.txt`, `reports/ingest.json`  
**output:** `chapters.jsonl`, `reports/chapters.json`

#### process

1. **build candidate list:** scan text line by line, flag potential chapter headers using patterns:
   ```
   ^\s*(chapter|rozdział)\s+(\d+|[ivxlcdm]+)\.?\s*(.*)$
   ^\s*(part|część|tom)\s+(\d+|[ivxlcdm]+)\.?\s*(.*)$
   ^\s*(prologue|epilogue|prolog|epilog)\s*$
   ^\s*[ivxlcdm]{1,8}\s*$
   ^[A-Z][A-Z\s]{5,50}$
   ^\s*\d{1,3}\.\s+[A-Z]
   ```
2. **toc cross-reference:** validate candidates against extracted toc entries
3. **position validation:** candidate must appear at position 0 or after blank line
4. **context validation:** examine 6 lines following candidate—accept if prose-like
5. **build spans:** for each accepted header, set char_start/char_end
6. **gap detection:** warn if any chapter > 20% of book
7. **fallback:** if zero chapters, create single "Full Text" chapter

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
| TARGET_CHARS | 600 | ideal chunk size |
| MIN_CHARS | 100 | minimum chunk size |
| MAX_CHARS | 1600 | hard maximum |

#### process

1. initialize `global_chunk_index = 0`
2. for each chapter:
   - extract text from raw_text using char offsets
   - split into paragraphs on `\n\n+`
   - unwrap hard-wrapped lines within paragraphs
   - convert paragraphs to units (sentence-split if > MAX_CHARS)
   - pack units into chunks ≤ MAX_CHARS
   - merge tiny chunks < MIN_CHARS with neighbors
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

**input:** `chunks.jsonl`, tts configuration  
**output:** `audio/chunks/*.mp3`, `playback_map.jsonl`, `reports/tts.json`

#### configuration

| parameter | description |
|-----------|-------------|
| voice_id | elevenlabs voice identifier |
| model | e.g., `eleven_multilingual_v2` |
| output_format | `mp3_44100_128` |
| concurrency | max parallel requests (default: 5) |
| retry_attempts | max retries per chunk (default: 3) |
| retry_backoff_base | base delay in seconds (default: 2) |

#### process

1. load progress from existing tts.json if partial
2. for each chunk:
   - skip if already completed
   - call elevenlabs api
   - save to `audio/chunks/{chunk_id}.mp3`
   - measure duration via ffprobe
   - write playback_map entry
3. use async with semaphore for concurrency
4. retry with exponential backoff on failures
5. sort playback_map.jsonl by chunk_index

#### resumability

fully resumable—rerun skips completed chunks, processes only missing/failed.

#### error handling

| condition | action |
|-----------|--------|
| api rate limit | backoff and retry |
| api server error (5xx) | backoff and retry |
| api client error (4xx) | log failure, skip chunk |
| audio file write fails | fail stage |
| ffprobe fails | log warning with duration_ms = -1 |

---

### stage 6: build rag index

**input:** `chunks.jsonl`, embedding configuration  
**output:** `rag/index.faiss`, `rag/meta.jsonl`, `reports/rag.json`

#### configuration

| parameter | description |
|-----------|-------------|
| embedding_model | e.g., `text-embedding-3-small` |
| embedding_dimensions | e.g., 1536 |
| batch_size | chunks per api call (default: 100) |
| index_type | faiss index type (default: `IndexFlatIP`) |

#### process

1. initialize faiss index
2. batch process chunks:
   - embed texts via openai api
   - normalize vectors (L2)
   - add to index
   - write meta.jsonl entries
3. save index to `rag/index.faiss`

#### runtime query contract

```python
def query_rag(question: str, current_chunk_index: int, k: int = 10, allow_spoilers: bool = False) -> list[Chunk]:
    query_embedding = embed_text(question)
    faiss.normalize_L2(query_embedding)
    distances, indices = index.search(query_embedding, k * 2)
    
    results = []
    for idx in indices[0]:
        meta = meta_lines[idx]
        if allow_spoilers or meta["chunk_index"] <= current_chunk_index:
            results.append(load_chunk(meta["chunk_id"]))
        if len(results) >= k:
            break
    return results
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

1. determine checkpoint positions: every N chunks + final
2. for each position:
   - gather previous checkpoint + new chunks
   - build prompt requesting json output
   - call llm, parse response
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

---

## pipeline orchestration

### cli interface

```bash
# full pipeline
lectorius-pipeline process --input book.epub --book-id b001 --output-dir ./books/b001

# individual stages
lectorius-pipeline ingest --input book.epub --output-dir ./books/b001
lectorius-pipeline chapterize --book-dir ./books/b001
lectorius-pipeline chunkify --book-dir ./books/b001
lectorius-pipeline validate --book-dir ./books/b001
lectorius-pipeline tts --book-dir ./books/b001 --voice-id abc123
lectorius-pipeline rag --book-dir ./books/b001
lectorius-pipeline memory --book-dir ./books/b001

# resume failed tts
lectorius-pipeline tts --book-dir ./books/b001 --resume

# reprocess from specific stage
lectorius-pipeline process --book-dir ./books/b001 --from-stage chunkify
```

### stage dependencies

```
ingest → chapterize → chunkify → validate → tts → [rag, memory]
                                              ↘      ↗
                                           (parallel)
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
  min_chars: 100
  max_chars: 1600
  sentence_splitter: spacy
  spacy_model_en: en_core_web_sm

tts:
  provider: elevenlabs
  voice_id: ${ELEVENLABS_VOICE_ID}
  model: eleven_multilingual_v2
  output_format: mp3_44100_128
  concurrency: 5
  retry_attempts: 3
  retry_backoff_base: 2

rag:
  embedding_provider: openai
  embedding_model: text-embedding-3-small
  embedding_dimensions: 1536
  batch_size: 100
  index_type: IndexFlatIP

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

## appendix: regex patterns

### chapter detection

```python
CHAPTER_PATTERNS = [
    r'^\s*(chapter|ch\.?)\s+(\d+|[ivxlcdm]+)\.?\s*(.*)$',
    r'^\s*(part|book)\s+(\d+|[ivxlcdm]+)\.?\s*(.*)$',
    r'^\s*(prologue|epilogue|introduction|preface|foreword|afterword)\s*$',
    r'^\s*(rozdzia[łl])\s+(\d+|[ivxlcdm]+)\.?\s*(.*)$',
    r'^\s*[ivxlcdm]{1,8}\s*$',
    r'^\s*\d{1,3}\.\s+[A-Z]',
]

ALL_CAPS_HEADER = r'^[A-Z][A-Z\s\-\']{5,50}$'
```

### sentence splitting (fallback)

```python
SENTENCE_END = r'(?<=[.!?])(?<![A-Z]\.)(?<!Mr\.)(?<!Mrs\.)(?<!Dr\.)\s+(?=[A-Z"])'
```

### page artifacts

```python
PAGE_NUMBER = r'^\s*\d{1,4}\s*$'
ROMAN_NUMERAL_LINE = r'^\s*[ivxlcdmIVXLCDM]{1,8}\s*$'
```
