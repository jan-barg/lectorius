## 1. overview

all api routes are implemented as sveltekit server endpoints, deployed to vercel functions.

**base url:** `https://{domain}/api`

**content types:**
- requests: `application/json` (except `/api/ask` which uses `multipart/form-data`)
- responses: `application/json`

**authentication:** none for mvp (public access)

---

## 2. endpoints summary

| method | endpoint | description |
|--------|----------|-------------|
| GET | `/api/books` | list all available books |
| GET | `/api/books/[id]` | get full book pack metadata |
| GET | `/api/books/[id]/audio/[chunk_id]` | get audio file for a chunk |
| GET | `/api/system/audio/[fallback_id]` | get pre-recorded fallback audio |
| POST | `/api/ask` | submit question, receive voice answer |

---

## 3. endpoint details

### 3.1 GET /api/books

list all available books in the library.

**response: 200 ok**
```json
{
  "books": [
    {
      "book_id": "great-gatsby",
      "title": "The Great Gatsby",
      "author": "F. Scott Fitzgerald",
      "cover_url": "https://supabase.../great-gatsby/cover.jpg",
      "total_chapters": 9,
      "total_duration_ms": 18000000
    }
  ]
}
```

**errors:**

| status | condition | body |
|--------|-----------|------|
| 500 | supabase connection failed | `{ "error": "Failed to fetch books" }` |

**implementation notes:**
- read `manifest.json` from each book folder in supabase storage
- cache response for 5 minutes
- derive `total_chapters` and `total_duration_ms` from `manifest.stats`

---

### 3.2 GET /api/books/[id]

get full book pack metadata. client loads this once when user selects a book.

**response: 200 ok**
```json
{
  "book": {
    "book_id": "great-gatsby",
    "title": "The Great Gatsby",
    "author": "F. Scott Fitzgerald",
    "language": "en",
    "year": 1925,
    "book_type": "fiction",
    "source": "gutenberg",
    "source_id": "pg64317"
  },
  "manifest": { ... },
  "chapters": [ ... ],
  "chunks": [ ... ],
  "playback_map": [ ... ],
  "checkpoints": [ ... ]
}
```

**errors:**

| status | condition | body |
|--------|-----------|------|
| 400 | invalid book_id format | `{ "error": "Invalid book ID" }` |
| 404 | book not found | `{ "error": "Book not found" }` |
| 500 | storage/parse error | `{ "error": "Failed to load book" }` |

**implementation notes:**
- fetch from supabase storage:
  - `books/{id}/book.json`
  - `books/{id}/manifest.json`
  - `books/{id}/chapters.jsonl`
  - `books/{id}/chunks.jsonl`
  - `books/{id}/playback_map.jsonl`
  - `books/{id}/memory/checkpoints.jsonl`
- parse jsonl files (newline-delimited json)

---

### 3.3 GET /api/books/[id]/audio/[chunk_id]

get audio file for a specific chunk.

**response: 302 redirect**
```
Location: https://{supabase}/storage/v1/object/public/books/great-gatsby/audio/chunks/great-gatsby_ch001_000001.mp3
```

**errors:**

| status | condition | body |
|--------|-----------|------|
| 400 | invalid chunk_id format | `{ "error": "Invalid chunk ID" }` |
| 404 | audio file not found | `{ "error": "Audio not found" }` |

**implementation notes:**
- use redirect to supabase public url (cdn-cached)
- validate that chunk_id belongs to book_id

---

### 3.4 GET /api/system/audio/[fallback_id]

get pre-recorded fallback audio.

**valid fallback_id values:** `error`, `book_only`, `no_context_yet`, `resuming`

**response: 302 redirect**
```
Location: https://{supabase}/storage/v1/object/public/system/audio/error.mp3
```

**errors:**

| status | condition | body |
|--------|-----------|------|
| 400 | invalid fallback_id | `{ "error": "Invalid fallback ID" }` |

---

### 3.5 POST /api/ask

main q&a endpoint. receives user's spoken question, returns voice answer.

**request (multipart/form-data):**
```
POST /api/ask
Content-Type: multipart/form-data

Fields:
- book_id: string
- chunk_index: number
- chunk_time_ms: number
- audio: File (webm or wav, max 10MB)
```

**request (alternative json with base64):**
```json
{
  "book_id": "great-gatsby",
  "chunk_index": 42,
  "chunk_time_ms": 2340,
  "audio_base64": "UklGRi..."
}
```

**response: 200 ok (success)**
```json
{
  "success": true,
  "question_text": "Who is Gatsby?",
  "answer_text": "Jay Gatsby is the mysterious millionaire who lives next door to Nick...",
  "answer_audio": "//uQxAAAAAANIAAAAAExBTUUzLjEw..."
}
```

**response: 200 ok (error with fallback)**
```json
{
  "success": false,
  "error": "LLM request failed",
  "fallback_audio_id": "error"
}
```

**errors:**

| status | condition | body |
|--------|-----------|------|
| 400 | missing required fields | `{ "success": false, "error": "Missing book_id", "fallback_audio_id": "error" }` |
| 400 | invalid book_id | `{ "success": false, "error": "Book not found", "fallback_audio_id": "error" }` |
| 400 | chunk_index out of range | `{ "success": false, "error": "Invalid chunk index", "fallback_audio_id": "error" }` |
| 400 | audio too large (>10mb) | `{ "success": false, "error": "Audio file too large", "fallback_audio_id": "error" }` |
| 500 | internal error | `{ "success": false, "error": "Internal error", "fallback_audio_id": "error" }` |

---

## 4. implementation flow (/api/ask)
```
1. validate request
   - check required fields
   - validate book_id exists
   - validate chunk_index in range

2. transcribe audio (whisper)
   POST https://api.openai.com/v1/audio/transcriptions
   - model: "whisper-1"
   - file: audio blob
   → question_text

3. check for early exit conditions
   - if chunk_index < 5: return fallback "no_context_yet"
   - if question is off-topic: return fallback "book_only"

4. assemble context
   a. load chunks around playhead (~60 seconds)
   b. load latest memory checkpoint ≤ chunk_index
   c. query rag (if needed), filter to chunk_index

5. call llm (claude)
   POST https://api.anthropic.com/v1/messages
   - model: "claude-sonnet-4-20250514"
   - system: [see llm prompt spec]
   → answer_text

6. generate speech (elevenlabs)
   POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}
   - model_id: "eleven_multilingual_v2"
   → answer_audio (bytes)

7. return response
   - encode audio as base64
   - return success response
```

---

## 5. context assembly

### 5.1 calculating "last 60 seconds"
```typescript
function getRecentChunks(
  playbackMap: PlaybackMapEntry[],
  chunks: Chunk[],
  currentChunkIndex: number,
  targetDurationMs: number = 60000
): Chunk[] {
  const result: Chunk[] = [];
  let totalDuration = 0;

  for (let i = currentChunkIndex; i >= 1 && totalDuration < targetDurationMs; i--) {
    const entry = playbackMap.find(p => p.chunk_index === i);
    if (entry) {
      result.unshift(chunks.find(c => c.chunk_index === i)!);
      totalDuration += entry.duration_ms;
    }
  }

  return result;
}
```

### 5.2 finding relevant checkpoint
```typescript
function getCurrentCheckpoint(
  checkpoints: MemoryCheckpoint[],
  currentChunkIndex: number
): MemoryCheckpoint | null {
  for (let i = checkpoints.length - 1; i >= 0; i--) {
    if (checkpoints[i].until_chunk_index <= currentChunkIndex) {
      return checkpoints[i];
    }
  }
  return null;
}
```

### 5.3 rag query (server-side)
```python
def query_rag(question: str, current_chunk_index: int, book_id: str, k: int = 5) -> list[Chunk]:
    index = faiss.read_index(f"books/{book_id}/rag/index.faiss")
    with open(f"books/{book_id}/rag/meta.jsonl") as f:
        meta = [json.loads(line) for line in f]

    embedding = embed_text(question)
    faiss.normalize_L2(embedding)
    distances, indices = index.search(embedding, k * 3)

    results = []
    for idx in indices[0]:
        if meta[idx]["chunk_index"] <= current_chunk_index:
            results.append(meta[idx]["chunk_id"])
        if len(results) >= k:
            break

    return load_chunks_by_ids(book_id, results)
```

---

## 6. rate limiting

for mvp, rely on vercel's built-in limits. future consideration:

| endpoint | limit | window |
|----------|-------|--------|
| `/api/ask` | 20 requests | per minute per ip |
| `/api/books` | 100 requests | per minute per ip |
| `/api/books/[id]` | 50 requests | per minute per ip |

---

## 7. error response format

all errors follow consistent format:
```typescript
interface ErrorResponse {
  error: string;
  code?: string;
  details?: unknown;
}
```

for `/api/ask`, errors include `fallback_audio_id` so client can play appropriate fallback.

---

## 8. cors configuration
```typescript
// hooks.server.ts
export const handle: Handle = async ({ event, resolve }) => {
  const response = await resolve(event);

  response.headers.set('Access-Control-Allow-Origin', '*');
  response.headers.set('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  response.headers.set('Access-Control-Allow-Headers', 'Content-Type');

  return response;
};
```

---

## 9. environment variables
```bash
# supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=xxx

# openai (whisper)
OPENAI_API_KEY=xxx

# anthropic (claude)
ANTHROPIC_API_KEY=xxx

# elevenlabs
ELEVENLABS_API_KEY=xxx
ELEVENLABS_VOICE_ID=xxx
```

---

## 10. file structure
```
apps/web/src/routes/api/
├── books/
│   ├── +server.ts                    # GET /api/books
│   └── [id]/
│       ├── +server.ts                # GET /api/books/[id]
│       └── audio/
│           └── [chunk_id]/
│               └── +server.ts        # GET /api/books/[id]/audio/[chunk_id]
├── system/
│   └── audio/
│       └── [fallback_id]/
│           └── +server.ts            # GET /api/system/audio/[fallback_id]
└── ask/
    └── +server.ts                    # POST /api/ask
