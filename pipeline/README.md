# lectorius pipeline

transforms epub files into structured audiobook packs — text extraction, chapter detection, sentence-aware chunking, multi-provider tts, pgvector embeddings, and ai-generated story memory checkpoints.

## quickstart

```bash
cd pipeline
python -m venv .venv
source .venv/bin/activate
pip install -e .

# optional: better sentence splitting
python -m spacy download en_core_web_sm
```

### environment variables

```bash
# required for tts (openai) and rag
OPENAI_API_KEY=sk-proj-...

# required for tts (elevenlabs) and generate-fallbacks
ELEVENLABS_API_KEY=sk_...

# required for --llm-assist (ingest) and memory stage
ANTHROPIC_API_KEY=sk-ant-...

# required for rag (pgvector) and generate-fallbacks (storage upload)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=xxx
```

### process a book end-to-end

```bash
# stages 1-4: ingest → chapterize → chunkify → validate
lectorius-pipeline process \
  --input ../source/pride-and-prejudice.epub \
  --book-id pride-and-prejudice \
  --output-dir ../books/pride-and-prejudice \
  --llm-assist \
  --tts-provider elevenlabs --voice-id <voice_id>

# stage 5: generate audio (reads provider/voice from book.json)
lectorius-pipeline tts --book-dir ../books/pride-and-prejudice

# stage 6: build pgvector search index
lectorius-pipeline rag --book-dir ../books/pride-and-prejudice

# stage 7: generate story memory checkpoints
lectorius-pipeline memory --book-dir ../books/pride-and-prejudice

# generate per-voice fallback audio (uploads to supabase storage)
lectorius-pipeline generate-fallbacks --book-dir ../books/pride-and-prejudice
```

### output

```
books/pride-and-prejudice/
├── manifest.json              # processing metadata
├── raw_text.txt               # normalized full text
├── book.json                  # title, author, language, tts_provider, voice_id
├── chapters.jsonl             # chapter boundaries with char offsets
├── chunks.jsonl               # ~600-char text chunks
├── playback_map.jsonl         # chunk → audio file mapping with durations
├── audio/
│   └── chunks/
│       └── {chunk_id}.mp3     # one mp3 per chunk
├── rag/
│   └── meta.jsonl             # vector_id → chunk_id mapping (embeddings in supabase)
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

the pipeline has 7 stages plus a standalone fallback generator. stages 1-4 run together via `process`. stages 5-7 run individually.

```
ingest → chapterize → chunkify → validate → tts → [rag, memory]  (parallel)

generate-fallbacks  (standalone, requires book.json or explicit flags)
```

### 1. ingest

parses the epub, strips gutenberg boilerplate, normalizes whitespace, fixes drop caps and hyphenation, removes page number artifacts, and strips title/byline from the text start.

with `--llm-assist`, additionally calls claude to:
- identify narrative start/end boundaries (trim front/back matter)
- detect junk patterns (illustration captions, repeated headers)
- identify the chapter heading format for downstream use

the llm call is non-blocking — if it fails, the pipeline continues with rule-based heuristics only. a 50% safety limit prevents catastrophic trimming from bad llm markers.

### 2. chapterize

scans the normalized text for chapter headings using a priority-ordered pattern list. if the ingest report contains an llm-detected chapter pattern, it's prepended as the highest-priority matcher. filters out drop cap false positives and mid-sentence boundary matches. merges tiny chapters (<500 chars) with neighbors.

### 3. chunkify

splits each chapter's text into ~600-character chunks that end on sentence boundaries. strips chapter headings from chunk text (already in metadata). merges tiny chunks and heading-only chunks with neighbors. uses spacy for sentence splitting (falls back to regex).

### 4. validate

checks all chunks for errors (empty text, too long, duplicate IDs, offset overlaps) and warnings (too short, offset gaps, non-prose content). errors halt the pipeline; warnings are logged.

### 5. tts (text-to-speech)

generates one mp3 per chunk. provider and voice are resolved from: cli flags → `book.json` → openai default.

| provider | model | default voice |
|----------|-------|---------------|
| openai | gpt-4o-mini-tts | nova |
| elevenlabs | eleven_multilingual_v2 | (from book.json voice_id) |

processes chunks with bounded async concurrency (default 5). retries failed chunks with exponential backoff. fully resumable — rerun skips completed chunks.

### 6. rag (retrieval-augmented generation)

embeds all chunks using openai `text-embedding-3-small` (1536 dimensions). normalizes vectors (L2) and inserts into the supabase `book_embeddings` table (pgvector). writes `rag/meta.jsonl` locally as a reference mapping.

at query time, the web app queries pgvector with spoiler-free filtering (`chunk_index <= current_position`).

### 7. memory (story checkpoints)

generates periodic story summaries with character, place, and plot thread tracking using claude sonnet. for small books (<100 chunks), checkpoints at 25%, 50%, 75%, 100%. for larger books, every 50 chunks.

each checkpoint contains:
- a 2-3 paragraph running summary
- people (name, aliases, role, description, first/last chunk)
- places (name, description, first/last chunk)
- plot threads (description, status open/resolved, chunk range)

### 8. generate fallback audio

standalone command that generates per-voice fallback mp3s and uploads them to supabase storage. these are pre-recorded error/refusal messages in the book's narrator voice.

| fallback | text | use case |
|----------|------|----------|
| `no_context_yet` | "i don't have enough context yet. let's keep reading." | question before chunk 5 |
| `error` | "i can't seem to find an answer right now." | api/tts failure |
| `book_only` | "i can only help with questions about this book." | off-topic question |

skips files that already exist in storage. books sharing the same `voice_id` share fallback files.

## cli reference

```bash
# full pipeline (stages 1-4)
lectorius-pipeline process --input FILE --book-id ID --output-dir DIR [OPTIONS]
  --llm-assist                         # use claude for text analysis
  --tts-provider openai|elevenlabs     # set in book.json
  --voice-id VOICE_ID                  # set in book.json
  --stop-after STAGE                   # stop after ingest|chapterize|chunkify|validate
  --from-stage STAGE                   # resume from a stage

# individual text processing stages
lectorius-pipeline ingest --input FILE --book-id ID --output-dir DIR [--llm-assist]
lectorius-pipeline chapterize --book-dir DIR --book-id ID
lectorius-pipeline chunkify --book-dir DIR --book-id ID
lectorius-pipeline validate --book-dir DIR --book-id ID

# audio generation (reads provider/voice from book.json if not specified)
lectorius-pipeline tts --book-dir DIR [--provider openai|elevenlabs] [--voice VOICE] [--model MODEL] [--resume] [--concurrency N]

# vector index (pgvector)
lectorius-pipeline rag --book-dir DIR [--model MODEL] [--batch-size N]

# story memory checkpoints
lectorius-pipeline memory --book-dir DIR [--model MODEL] [--interval N]

# per-voice fallback audio
lectorius-pipeline generate-fallbacks [--book-dir DIR] [--provider openai|elevenlabs] [--voice VOICE]
```

### defaults

| option | default |
|--------|---------|
| tts provider | reads from book.json, falls back to openai |
| tts model (openai) | gpt-4o-mini-tts |
| tts model (elevenlabs) | eleven_multilingual_v2 |
| tts voice (openai) | nova |
| tts concurrency | 5 |
| embedding model | text-embedding-3-small |
| embedding batch size | 100 |
| memory llm model | claude-sonnet-4-20250514 |
| checkpoint interval | 50 chunks |
| chunk target size | 600 chars |

## costs

tts dominates. elevenlabs sounds significantly better but costs ~20x more.

| stage | provider | rate |
|-------|----------|------|
| ingest (--llm-assist) | anthropic sonnet | ~$0.02/book |
| tts | openai gpt-4o-mini-tts | $15/1M chars |
| tts | elevenlabs | ~$300/1M chars (quota-based) |
| rag | openai embeddings | ~$0.01/book |
| memory | anthropic sonnet | ~$0.50-2.00/book |

a typical book (~500k chars) costs ~$7.50 with openai tts or ~$150 with elevenlabs.

## tested books

| book | author | chapters | chunks | tts provider |
|------|--------|----------|--------|-------------|
| pride and prejudice | jane austen | 61 | 1398 | openai (nova) |
| a christmas carol | charles dickens | 5 | ~200 | elevenlabs |
| the metamorphosis | franz kafka | 3 | ~150 | openai (alloy) |
| rip van winkle | washington irving | 3 | 83 | elevenlabs |

## how --llm-assist works

the pipeline sends the first ~4000 and last ~3000 characters of the normalized text to claude. claude returns structured json:

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

- `narrative_start/end_marker` — trims front/back matter with fuzzy matching. 50% safety limit prevents catastrophic trimming from bad markers
- `junk_patterns` — compiled as regexes and stripped during ingest
- `chapter_heading_pattern` — saved in `reports/ingest.json`, loaded by chapterize as the highest-priority detection pattern
- the call is non-blocking — pipeline continues with rule-based heuristics if it fails

## post-processing: llm validation

digitized books vary wildly in quality. for production results, run the output through an llm validation pass after processing.

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

**how to run it:**

1. process the book through the full pipeline
2. feed `chapters.jsonl` and `chunks.jsonl` to an llm for review. for large books, sample the first and last 20 chunks plus a random selection from the middle
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

see [docs/pipeline.md](../docs/pipeline.md) for the complete pipeline specification including all schemas, stage details, error handling, and configuration options.
