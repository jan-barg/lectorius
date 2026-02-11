# lectorius pipeline

transforms epub files into structured "book packs" for the lectorius audiobook app. the pipeline extracts text, detects chapters, splits into chunks, generates audio, builds a semantic search index, and creates story memory checkpoints.

## quickstart

```bash
cd pipeline
python -m venv .venv
source .venv/bin/activate
pip install -e .

# download spacy model (optional, regex fallback used if missing)
python -m spacy download en_core_web_sm
```

### environment variables

create a `.env` file in the project root:

```bash
# required for --llm-assist (ingest) and memory stage
ANTHROPIC_API_KEY=sk-ant-...

# required for tts and rag stages
OPENAI_API_KEY=sk-proj-...

# required for elevenlabs tts (optional — openai works for dev)
ELEVENLABS_API_KEY=sk_...
ELEVENLABS_VOICE_ID=...
```

### process a book end-to-end

```bash
# load env vars
export $(grep -v '^#' ../.env | xargs)

# stages 1-4: ingest → chapterize → chunkify → validate
lectorius-pipeline process \
  --input ../source/the-great-gatsby.epub \
  --book-id great-gatsby \
  --output-dir ../books/great-gatsby \
  --llm-assist

# stage 5: generate audio
lectorius-pipeline tts --book-dir ../books/great-gatsby

# stage 6: build semantic search index
lectorius-pipeline rag --book-dir ../books/great-gatsby

# stage 7: generate story memory checkpoints
lectorius-pipeline memory --book-dir ../books/great-gatsby
```

### output

```
books/great-gatsby/
├── manifest.json              # processing metadata
├── raw_text.txt               # normalized full text
├── book.json                  # title, author, language
├── chapters.jsonl             # chapter boundaries with char offsets
├── chunks.jsonl               # ~600-char text chunks
├── playback_map.jsonl         # chunk → audio file mapping
├── audio/
│   └── chunks/
│       └── {chunk_id}.mp3     # one mp3 per chunk
├── rag/
│   ├── index.faiss            # FAISS vector index
│   └── meta.jsonl             # vector_id → chunk_id mapping
├── memory/
│   └── checkpoints.jsonl      # periodic story summaries + entities
└── reports/
    ├── ingest.json
    ├── chapters.json
    ├── chunks.json
    ├── validation.json
    ├── tts.json
    ├── rag.json
    └── memory.json
```

## stages

the pipeline has 7 stages. stages 1-4 run together via `process`. stages 5-7 run individually.

### 1. ingest

parses the epub, strips gutenberg boilerplate, normalizes whitespace, fixes drop caps and hyphenation, removes page number artifacts, and strips title/byline from the text start.

with `--llm-assist`, additionally calls claude sonnet to:
- identify narrative start/end boundaries (trim front/back matter)
- detect junk patterns (illustration captions, repeated headers)
- identify the chapter heading format for downstream use

the LLM call is non-blocking — if it fails, the pipeline continues with rule-based heuristics only.

### 2. chapterize

scans the normalized text for chapter headings using a priority-ordered pattern list. if the ingest report contains an LLM-detected chapter pattern, it's prepended as the highest-priority matcher. filters out drop cap false positives and mid-sentence boundary matches. merges tiny chapters (<500 chars) with neighbors.

### 3. chunkify

splits each chapter's text into ~600-character chunks that end on sentence boundaries. strips chapter headings from chunk text (already in metadata). merges tiny chunks and heading-only chunks with neighbors. uses spacy for sentence splitting (falls back to regex).

### 4. validate

checks all chunks for errors (empty text, too long, duplicate IDs, offset overlaps) and warnings (too short, offset gaps, non-prose content). errors halt the pipeline; warnings are logged.

### 5. tts (text-to-speech)

generates one mp3 per chunk using OpenAI or ElevenLabs. processes chunks with bounded async concurrency (default 5). retries failed chunks with exponential backoff. writes `playback_map.jsonl` mapping each chunk to its audio file and duration.

fully resumable — rerun skips completed chunks, only processes pending/failed.

### 6. rag (retrieval-augmented generation)

embeds all chunks using OpenAI `text-embedding-3-small` (1536 dimensions). normalizes vectors (L2) and builds a FAISS `IndexFlatIP` index for cosine similarity search. writes `rag/index.faiss` and `rag/meta.jsonl` linking vector IDs to chunk IDs.

at query time, the index supports spoiler-free retrieval by filtering results to chunks at or before the reader's current position.

### 7. memory (story checkpoints)

generates periodic story summaries with character, place, and plot thread tracking using claude sonnet. for small books (<100 chunks), checkpoints at 25%, 50%, 75%, 100%. for larger books, every 50 chunks.

each checkpoint contains:
- a 2-3 paragraph running summary
- people (name, aliases, role, description, first/last chunk)
- places (name, description, first/last chunk)
- plot threads (description, status open/resolved, chunk range)

## cli reference

```bash
# full pipeline (stages 1-4)
lectorius-pipeline process --input FILE --book-id ID --output-dir DIR [OPTIONS]

# individual stages (1-4)
lectorius-pipeline ingest --input FILE --book-id ID --output-dir DIR [--llm-assist]
lectorius-pipeline chapterize --book-dir DIR --book-id ID
lectorius-pipeline chunkify --book-dir DIR --book-id ID
lectorius-pipeline validate --book-dir DIR --book-id ID

# stage 5: tts
lectorius-pipeline tts --book-dir DIR [--provider openai|elevenlabs] [--voice VOICE] [--model MODEL] [--resume] [--concurrency N]

# stage 6: rag
lectorius-pipeline rag --book-dir DIR [--model MODEL] [--batch-size N]

# stage 7: memory
lectorius-pipeline memory --book-dir DIR [--model MODEL] [--interval N]
```

### common options

| flag | description |
|------|-------------|
| `--input` | path to epub file |
| `--book-id` | identifier (lowercase, hyphens ok) |
| `--output-dir` / `--book-dir` | output directory for book pack |
| `--llm-assist` | use claude for text structure analysis (ingest) |
| `--stop-after STAGE` | stop after ingest/chapterize/chunkify/validate |
| `--from-stage STAGE` | resume from a stage (needs prior outputs) |
| `-v, --verbose` | debug-level logging |

### tts options

| flag | description |
|------|-------------|
| `--provider` | `openai` (default) or `elevenlabs` |
| `--voice` | openai: alloy/echo/fable/onyx/nova/shimmer. elevenlabs: voice_id |
| `--model` | openai: tts-1/tts-1-hd. elevenlabs: eleven_multilingual_v2 |
| `--resume` | skip already-completed chunks |
| `--concurrency` | max parallel API requests (default: 5) |

### rag options

| flag | description |
|------|-------------|
| `--model` | embedding model (default: text-embedding-3-small) |
| `--batch-size` | chunks per API call (default: 100) |

### memory options

| flag | description |
|------|-------------|
| `--model` | LLM model (default: claude-sonnet-4-20250514) |
| `--interval` | chunks between checkpoints (default: 50) |

## costs

tts dominates costs. elevenlabs is ~20x more expensive than openai but sounds significantly better.

### per-stage rates

| stage | provider | rate |
|-------|----------|------|
| ingest (--llm-assist) | anthropic sonnet | ~$0.01-0.03/book (one API call) |
| tts | openai tts-1 | $15/1M chars |
| tts | openai tts-1-hd | $30/1M chars |
| tts | elevenlabs | ~$300/1M chars (quota-based) |
| rag | openai embeddings | $0.02/1M tokens (~negligible) |
| memory | anthropic sonnet | ~$0.01-0.02/checkpoint |

### real cost examples

| book | chars | openai tts-1 | openai tts-1-hd | elevenlabs | rag + memory | total (dev) | total (prod) |
|------|-------|-------------|----------------|------------|-------------|-------------|--------------|
| rip van winkle | 43k | $0.64 | $1.28 | $12.80 | ~$0.06 | **~$0.72** | **~$12.89** |
| yellow wallpaper | 31k | $0.47 | $0.94 | $9.40 | ~$0.06 | **~$0.55** | **~$9.49** |
| great gatsby | 267k | $4.00 | $8.00 | $80.01 | ~$0.17 | **~$4.20** | **~$80.21** |
| pride & prejudice | 684k | $10.27 | $20.53 | $205.30 | ~$0.65 | **~$10.95** | **~$205.98** |

## how --llm-assist works

the pipeline sends the first ~4000 and last ~3000 characters of the normalized text to claude sonnet. claude returns a structured JSON analysis:

```json
{
  "narrative_start_marker": "It is a truth universally acknowledged...",
  "narrative_end_marker": "...had been the means of uniting them.",
  "junk_patterns": ["\\[Illustration:.*?\\]"],
  "chapter_heading_pattern": "^CHAPTER\\s+[IVXLC]+\\.$",
  "chapter_heading_examples": ["CHAPTER I.", "CHAPTER II."],
  "anomalies": ["Drop cap letters on separate lines"]
}
```

**what happens with it:**
- `narrative_start_marker` / `narrative_end_marker` — used during ingest to trim front/back matter. fuzzy matching handles whitespace and case differences. a 50% safety limit prevents catastrophic trimming if the LLM returns a bad marker.
- `junk_patterns` — compiled as regexes and stripped from text during ingest.
- `chapter_heading_pattern` — saved in `reports/ingest.json` and loaded by the chapterize stage as the highest-priority detection pattern. patterns that match empty/blank strings are rejected.
- the LLM call is **non-blocking** — if it fails, the pipeline continues with rule-based heuristics only.

## tested books

| book | chapters | chunks | tts audio | rag vectors | memory checkpoints |
|------|----------|--------|-----------|-------------|-------------------|
| the great gatsby | 9 | 540 | — | — | — |
| pride and prejudice | 61 | 1398 | — | — | — |
| rip van winkle | 3 | 83 | ~44 min | 83 | 4 (18 people, 12 places, 5 threads) |
| the yellow wallpaper | 1 | 58 | ~32 min | 58 | 4 (11 people, 3 places, 6 threads) |

## post-processing: LLM validation pass

the pipeline handles most formatting issues automatically, but digitized books vary wildly in quality. for production-grade results, we recommend running the output through an LLM validation pass after the pipeline completes.

use the following prompt with claude (or another capable model), providing it the `chunks.jsonl` and `chapters.jsonl` files:

---

<details>
<summary><b>recommended validation prompt</b> (click to expand)</summary>

```
You are a quality-assurance reviewer for an audiobook text pipeline. You have been
given the processed output of a book that was digitized from an epub file. Your job
is to review the chapters and chunks for issues that would sound wrong when read
aloud by a text-to-speech engine.

BOOK: {book_title} by {book_author}

I will provide you with:
1. chapters.jsonl — one JSON object per line, each with chapter_id, title, char_start, char_end
2. chunks.jsonl — one JSON object per line, each with chunk_id, chapter_id, chunk_index, text, char_start, char_end

Review the data for the following issues and report them in a structured format:

CHAPTER-LEVEL CHECKS:
- Are chapter titles reasonable? Flag any that look like artifacts (single letters,
  gibberish, formatting remnants like "CHAPTER II.CHAPTER III.")
- Do chapter boundaries make narrative sense? Flag any chapter that seems to start
  or end mid-sentence or mid-paragraph.
- Are there missing chapters? Compare the chapter sequence against the expected
  numbering (I, II, III... or 1, 2, 3...) and flag gaps.

CHUNK-LEVEL CHECKS:
- Does any chunk contain non-narrative text that would sound wrong read aloud?
  Examples: illustration captions ("[Illustration: ...]"), page headers/footers,
  printer marks, table of contents fragments, publisher advertisements, transcriber
  notes, colophon text.
- Does any chunk start with a chapter heading that should have been stripped?
  (e.g., "CHAPTER V. Mr. Bennet was so..." — the heading should not be in the text)
- Does any chunk contain broken words from formatting artifacts?
  (e.g., "M R. Bennet" instead of "MR. Bennet", or "dur- ing" with a stray hyphen)
- Does the first chunk of the book start with the actual narrative prose? Flag if it
  starts with front matter (title pages, dedications, illustration lists, prefaces
  that aren't part of the story).
- Does the last chunk of the book end with the actual narrative prose? Flag if it
  contains back matter (printer info, transcriber notes, advertisements).
- Are there any chunks that are suspiciously short (<100 chars) or contain only
  whitespace/punctuation?

OUTPUT FORMAT:
Return a JSON object:
{
  "book_id": "...",
  "overall_quality": "good" | "needs_fixes" | "poor",
  "chapter_issues": [
    {"chapter_id": "...", "issue": "...", "severity": "error" | "warning", "suggestion": "..."}
  ],
  "chunk_issues": [
    {"chunk_id": "...", "chunk_index": N, "issue": "...", "severity": "error" | "warning",
     "current_text_snippet": "first 100 chars...", "suggested_fix": "..."}
  ],
  "summary": "1-2 sentence overall assessment"
}

Be thorough but practical. Only flag real issues that would affect the listening
experience. Do not flag stylistic choices or archaic language — only formatting
artifacts and pipeline errors.
```

</details>

---

**how to run it:**

1. process the book through the full pipeline (stages 1-7)
2. feed `chapters.jsonl` and `chunks.jsonl` to an LLM for review. for large books, sample the first and last 20 chunks plus a random selection from the middle.
3. fix any issues flagged — typically edit `raw_text.txt` and re-run from chapterize:
   ```bash
   lectorius-pipeline process --input source/book.epub --book-id my-book \
     --output-dir books/my-book --from-stage chapterize
   ```

## development

```bash
pip install -e ".[dev]"
pytest
ruff check .
mypy src/
```

## full specification

see [docs/pipeline.md](../docs/pipeline.md) for the complete pipeline specification including all schemas, error handling, and configuration options.
