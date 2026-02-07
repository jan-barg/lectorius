# lectorius pipeline

transforms epub files into structured "book packs" for the lectorius audiobook app. the pipeline extracts text, detects chapters, splits into chunks suitable for TTS, and validates the output.

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

create a `.env` file in the project root (or export directly):

```bash
# required for --llm-assist
ANTHROPIC_API_KEY=sk-ant-...
```

### run the pipeline

```bash
# basic run (rule-based only)
lectorius-pipeline process \
  --input ../source/the-great-gatsby.epub \
  --book-id great-gatsby \
  --output-dir ../books/great-gatsby

# recommended: with LLM-assisted analysis
source ../.env  # or: export ANTHROPIC_API_KEY=...
lectorius-pipeline process \
  --input ../source/the-great-gatsby.epub \
  --book-id great-gatsby \
  --output-dir ../books/great-gatsby \
  --llm-assist
```

### output

```
books/great-gatsby/
├── manifest.json          # processing metadata
├── raw_text.txt           # normalized full text
├── book.json              # title, author, language
├── chapters.jsonl         # chapter boundaries with char offsets
├── chunks.jsonl           # ~600-char text chunks for TTS
└── reports/
    ├── ingest.json        # extraction stats, LLM analysis
    ├── chapters.json      # chapter detection report
    └── chunks.json        # chunking stats
```

## stages

the pipeline runs 4 stages sequentially:

### 1. ingest

parses the epub, strips gutenberg boilerplate, normalizes whitespace, fixes drop caps and hyphenation, removes page number artifacts, and strips title/byline from the text start.

with `--llm-assist`, additionally calls claude sonnet to:
- identify narrative start/end boundaries (trim front/back matter)
- detect junk patterns (illustration captions, repeated headers)
- identify the chapter heading format for downstream use

cost: ~$0.01-0.03 per book.

### 2. chapterize

scans the normalized text for chapter headings using a priority-ordered pattern list. if the ingest report contains an LLM-detected chapter pattern, it's prepended as the highest-priority matcher. filters out drop cap false positives and mid-sentence boundary matches. merges tiny chapters (<500 chars) with neighbors.

### 3. chunkify

splits each chapter's text into ~600-character chunks that end on sentence boundaries. strips chapter headings from chunk text (already in metadata). merges tiny chunks and heading-only chunks with neighbors.

### 4. validate

checks all chunks for errors (empty text, too long, duplicate IDs, offset overlaps) and warnings (too short, offset gaps, non-prose content). errors halt the pipeline; warnings are logged.

## cli reference

```bash
# full pipeline
lectorius-pipeline process --input FILE --book-id ID --output-dir DIR [OPTIONS]

# individual stages
lectorius-pipeline ingest --input FILE --book-id ID --output-dir DIR [--llm-assist]
lectorius-pipeline chapterize --book-dir DIR --book-id ID
lectorius-pipeline chunkify --book-dir DIR --book-id ID
lectorius-pipeline validate --book-dir DIR --book-id ID
```

### options

| flag | description |
|------|-------------|
| `--input` | path to epub file |
| `--book-id` | identifier (lowercase, hyphens ok) |
| `--output-dir` | output directory for book pack |
| `--llm-assist` | use claude for text structure analysis |
| `--stop-after STAGE` | stop after ingest/chapterize/chunkify/validate |
| `--from-stage STAGE` | resume from a stage (needs prior outputs) |
| `-v, --verbose` | debug-level logging |

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
- `chapter_heading_pattern` — saved in `reports/ingest.json` and loaded by the chapterize stage as the highest-priority detection pattern.
- the LLM call is **non-blocking** — if it fails, the pipeline continues with rule-based heuristics only.

## tested books

| book | chapters | chunks | notes |
|------|----------|--------|-------|
| the great gatsby | 9 | 540 | first chunk: "In my younger and more vulnerable years..." |
| pride and prejudice | 61 | 1398 | handles drop caps, missing-space headers (CHAPTERXXVII) |
| rip van winkle | 3 | 83 | short story with postscript section |

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

1. process the book through the pipeline:
   ```bash
   lectorius-pipeline process --input source/book.epub --book-id my-book \
     --output-dir books/my-book --llm-assist
   ```

2. feed the output to an LLM for review. you can provide `chapters.jsonl` and `chunks.jsonl` directly, or for large books, sample the first and last 20 chunks plus a random selection from the middle.

3. fix any issues flagged by the LLM — typically this means editing `raw_text.txt` and re-running from chapterize:
   ```bash
   lectorius-pipeline process --input source/book.epub --book-id my-book \
     --output-dir books/my-book --from-stage chapterize
   ```

this validation pass catches edge cases that the automated pipeline can't: book-specific formatting quirks, edition-specific artifacts, and OCR errors that vary from source to source.

## development

```bash
pip install -e ".[dev]"
pytest
ruff check .
mypy src/
```

## full specification

see [docs/pipeline.md](../docs/pipeline.md) for the complete pipeline specification including all schemas, error handling, and downstream stages (TTS, RAG, memory checkpoints).
