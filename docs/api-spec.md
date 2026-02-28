# lectorius — api specification

**version:** 1.2
**status:** draft
**last updated:** february 2026

---

## 1. overview

all api routes are implemented as sveltekit server endpoints, deployed to vercel functions.

**base url:** `https://{domain}/api`

**content types:**
- requests: `application/json`
- responses: `application/json` (except `/api/ask` which returns `text/event-stream` SSE)

**authentication:**
- access code system — users enter a code (verified against `access_codes` table), stored as an httpOnly cookie (`lectorius_access`)
- free-tier — unauthenticated users get 3 questions per IP (tracked in `question_log`)
- rate limiting — 60 requests/hour per user via upstash redis (sliding window)

---

## 2. endpoints summary

| method | endpoint | description |
|--------|----------|-------------|
| GET | `/api/books` | list all available books |
| GET | `/api/books/[id]` | get full book pack metadata |
| POST | `/api/ask` | submit question, receive streamed voice answer (SSE) |
| POST | `/api/verify-code` | validate access code, set auth cookie |
| GET | `/api/music/playlists` | list music playlists with songs |

audio files (chunk audio, fallback audio) are served directly from supabase storage public URLs — no API proxy endpoints.

---

## 3. endpoint details

### 3.1 GET /api/books

list all available books in the library.

**response: 200 ok**
```json
{
  "books": [
    {
      "book_id": "pride-and-prejudice",
      "title": "Pride and Prejudice",
      "author": "Jane Austen",
      "cover_url": "https://{supabase}/storage/v1/object/public/books/pride-and-prejudice/cover.jpg",
      "cover_video_url": "https://{supabase}/storage/v1/object/public/books/pride-and-prejudice/cover.mp4",
      "total_chapters": 24,
      "total_chunks": 1847,
      "total_duration_ms": 3542000,
      "status": "available"
    }
  ]
}
```

**errors:**

| status | condition | body |
|--------|-----------|------|
| 500 | supabase connection failed | error message from exception |

**implementation notes:**
- lists book folders in supabase `books` storage bucket
- loads `book.json` and `manifest.json` in parallel for each folder
- 5-minute in-memory cache on the book list
- skips folders where either file fails to load (graceful degradation)
- `cover_video_url` points to `cover.mp4` in the book's storage folder

---

### 3.2 GET /api/books/[id]

get full book pack metadata. client loads this once when user selects a book.

**response: 200 ok**
```json
{
  "book": {
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
  },
  "chapters": [ ... ],
  "chunks": [ ... ],
  "playback_map": [ ... ],
  "checkpoints": [ ... ],
  "cover_video_url": "https://{supabase}/storage/v1/object/public/books/pride-and-prejudice/cover.mp4"
}
```

**errors:**

| status | condition | body |
|--------|-----------|------|
| 404 | book not found or load error | error message from exception |

**implementation notes:**
- parallel fetch from supabase `books` storage bucket:
  - `{id}/book.json`
  - `{id}/chapters.jsonl`
  - `{id}/chunks.jsonl`
  - `{id}/playback_map.jsonl`
  - `{id}/memory/checkpoints.jsonl` (returns `[]` on error)
- playback_map `audio_path` entries are enhanced with full supabase storage URLs
- parse jsonl files (newline-delimited json)
- book detail is cached in-memory with 5-minute TTL (`getCachedBook`)

---

### 3.3 POST /api/ask

main q&a endpoint. receives user's spoken question, returns a streamed voice answer via server-sent events (SSE). each sentence is spoken individually as it's generated.

**request headers:**
- `x-user-name` (optional) — user's display name (trimmed to 100 chars)

**request body (JSON):**
```json
{
  "book_id": "pride-and-prejudice",
  "chunk_index": 42,
  "audio_base64": "UklGRi..."
}
```

| field | type | validation |
|-------|------|------------|
| `book_id` | string | non-empty |
| `chunk_index` | integer | >= 1 |
| `audio_base64` | string | base64-encoded webm, max 5MB (`length <= 5_000_000`) |

**response: 200 ok (text/event-stream)**

each SSE message is `data: {json}\n\n`. message types sent in order:

```typescript
// 1. transcribed question
{ type: 'question', text: string }

// 2. audio for each sentence (streamed as claude generates)
{ type: 'audio', text: string, audio: string }    // audio = base64 mp3

// 3. completion
{ type: 'done', full_answer: string }

// 4. error (replaces above if something fails)
{ type: 'error', error?: string, fallback_audio_url: string }
```

**pre-endpoint errors (from hooks middleware):**

these are returned as JSON before the endpoint runs:

| status | condition | body |
|--------|-----------|------|
| 429 | rate limit exceeded (60/hr) | `{ "error": "Too many questions. Try again later." }` |
| 403 | free-tier quota exhausted (3 questions) | `{ "error": "Free limit reached" }` |
| 503 | database unavailable for quota check | `{ "error": "Service temporarily unavailable" }` |

**in-stream errors (returned as SSE):**

| condition | fallback id |
|-----------|-------------|
| audio too large | `error` (no voice — book not yet loaded) |
| invalid book_id or book not found | `error` (no voice) |
| invalid chunk_index | `error` (no voice) |
| transcription failed | `error` (with book's voice) |
| could not understand audio | `error` (with book's voice) |
| chunk_index < 5 (not enough context) | `no_context_yet` (with book's voice) |
| stream/LLM/TTS failure | `error` (with book's voice) |

**per-voice fallback audio:**

fallback URLs are resolved per-book voice. if the book has a `voice_id`, fallback URLs point to per-voice recordings:
```
{SUPABASE_URL}/storage/v1/object/public/system/fallback-audio/{voice_id}/{id}.mp3
```
otherwise, generic fallbacks are used:
```
{SUPABASE_URL}/storage/v1/object/public/system/audio/{id}.mp3
```

**question logging:**

after a successful answer, the question is logged to the `question_log` table:
```json
{ "ip": "...", "user_name": "Alice", "book_id": "pride-and-prejudice", "question": "Who is Mr. Darcy?" }
```

---

### 3.4 POST /api/verify-code

validate an access code and set an auth cookie for unlimited Q&A access.

**request body (JSON):**
```json
{
  "code": "MYCODE123",
  "user_name": "Alice"
}
```

| field | type | required |
|-------|------|----------|
| `code` | string | yes (non-empty) |
| `user_name` | string | no |

**response: 200 ok**
```json
{ "success": true }
```

**errors:**

| status | condition | body |
|--------|-----------|------|
| 400 | missing or empty code | `{ "success": false, "error": "Missing code" }` |
| 401 | code not found in `access_codes` table | `{ "success": false, "error": "Invalid code" }` |
| 500 | database error | `{ "success": false, "error": "Server error" }` |

**implementation notes:**
- validates code against `access_codes` table via `maybeSingle()` query
- logs usage to `code_usage_log` table (code, IP, user_name)
- sets httpOnly cookie `lectorius_access`:
  - path: `/`, httpOnly: `true`, secure: `true` (prod), sameSite: `lax`, maxAge: 30 days

---

### 3.5 GET /api/music/playlists

list all music playlists with their songs. used by the ambient music player.

**response: 200 ok**
```json
{
  "playlists": [
    {
      "playlist_id": "ambient-classical",
      "name": "Classical Ambient",
      "type": "general",
      "book_id": null,
      "songs": [
        {
          "title": "Moonlight Sonata",
          "file_url": "https://{supabase}/storage/v1/object/public/system/music/ambient-classical/01-moonlight-sonata.mp3"
        }
      ]
    }
  ]
}
```

**errors:**

| status | condition | body |
|--------|-----------|------|
| 500 | database error | error message from exception |

**implementation notes:**
- queries `playlists` table for metadata (playlist_id, name, type, book_id, folder_path)
- lists `.mp3` files from supabase `system` storage bucket at each playlist's `folder_path`
- song titles are derived from filenames: strip `.mp3`, remove leading numbers/separators, replace hyphens/underscores with spaces, title-case
- playlists with no songs are excluded
- `Cache-Control: public, max-age=300` (5 minutes)

---

## 4. implementation flow (/api/ask)

the endpoint uses a streaming architecture: claude's response is streamed token-by-token, sentences are extracted as they form, each sentence is TTS'd individually, and the resulting audio is pushed to the client via SSE.

```
[hooks middleware]
1. rate limit check (upstash redis, 60/hr sliding window)
   - identifier: access code if present, else ip:{client_ip}
   - fail open on redis errors
   → 429 if exceeded

2. access code validation
   - check lectorius_access cookie against access_codes table
   - if invalid: delete cookie, fall through to free-tier check
   → sets validAccess flag

3. free-tier quota check (only if no valid access code)
   - count rows in question_log where ip = client_ip
   → 403 if count >= 3
   → 503 if database unavailable

[endpoint]
4. validate request
   - audio_base64 length <= 5,000,000
   - book_id is non-empty string
   - chunk_index is integer >= 1
   → SSE error with generic fallback on failure

5. load book data (in-memory cache, 5-min TTL)
   - resolve tts_provider and voice_id from book.json
   → SSE error if book not found

6. transcribe audio (whisper)
   - model: "whisper-1"
   - convert base64 webm → File via openai toFile()
   → SSE error if transcription fails or question < 2 chars

7. early exit: chunk_index < 5
   → SSE error "no_context_yet" (with book's voice)

8. assemble context
   a. getRecentChunks() — ~60 seconds of audio context
   b. getCurrentCheckpoint() — latest memory checkpoint ≤ chunk_index
   c. queryRAG() — pgvector similarity search (if shouldUseRAG() is true)
      - skips for greetings, meta questions, simple definitions
      - filters results to chunks at/before current index (spoiler prevention)

9. stream claude response → sentence-by-sentence TTS
   - model: "claude-sonnet-4-20250514", max_tokens: 500
   - extract sentences via regex as tokens arrive
   - for each sentence: TTS → send SSE { type: 'audio', text, audio }
   - TTS provider: book's tts_provider (fallback to openai on failure)
   - flush remaining buffer after stream ends

10. log question to question_log table

11. send { type: 'done', full_answer }
```

#### tts provider selection (web app)

| provider | model | default voice | use case |
|----------|-------|---------------|----------|
| openai | `gpt-4o-mini-tts` | `nova` | default / fallback |
| elevenlabs | `eleven_flash_v2_5` | (from book.json `voice_id`) | production, low latency |

the web app uses `eleven_flash_v2_5` (not `eleven_multilingual_v2` used in the pipeline) for lower latency during live Q&A.

if the book's TTS provider fails, the endpoint falls back to openai `gpt-4o-mini-tts` with the `nova` voice.

---

## 5. context assembly

all context functions are in `apps/web/src/lib/server/context.ts` and `apps/web/src/lib/server/rag.ts`.

### 5.1 recent chunks (~60 seconds of audio)
```typescript
function getRecentChunks(
  chunks: Chunk[],
  playbackMap: PlaybackMapEntry[],
  currentChunkIndex: number,
  targetDurationMs: number = 60000
): Chunk[]
```

builds Map lookups from chunks and playbackMap, then walks backwards from `currentChunkIndex` accumulating duration until ~60 seconds.

### 5.2 finding relevant checkpoint
```typescript
function getCurrentCheckpoint(
  checkpoints: MemoryCheckpoint[],
  currentChunkIndex: number
): MemoryCheckpoint | null
```

walks checkpoints in reverse, returns the latest where `until_chunk_index <= currentChunkIndex`.

### 5.3 rag query (pgvector)
```typescript
async function queryRAG(
  bookId: string,
  question: string,
  maxChunkIndex: number,
  limit: number = 5
): Promise<{ chunk_id: string; chunk_index: number; chapter_id: string }[]>
```

1. embed question with openai `text-embedding-3-small`
2. call supabase RPC `match_embeddings`:
   - `query_embedding`: question embedding vector
   - `match_book_id`: filter to this book
   - `max_chunk_index`: spoiler filter (only chunks at/before current position)
   - `match_count`: max results (default 5)
3. returns chunk metadata; errors are logged and return `[]` (fail gracefully)

### 5.4 rag decision logic
```typescript
function shouldUseRAG(question: string): boolean
```

returns `false` (skips RAG) for:
- greetings: `/^(hi|hello|hey|thanks|thank you)\b/i`
- meta questions: `/^what can you do|^how does this (work|app)/i`
- simple definitions: `/^(what does .{1,30} mean|define \w+)\??$/i`

returns `true` for everything else (default is to use RAG).

---

## 6. hooks middleware

`hooks.server.ts` intercepts all requests. only `POST /api/ask` is processed; all other routes pass through immediately.

### processing order

```
1. rate limit (upstash redis)
   - sliding window: 60 requests per 1 hour
   - identifier: access code cookie if present, else "ip:{client_ip}"
   - lazy-initialized singleton (created on first use)
   - if UPSTASH_REDIS env vars missing: logs warning, rate limiting disabled
   - if redis errors: logs error, fails open (user not blocked)
   → 429 if exceeded

2. access code validation
   - reads lectorius_access cookie
   - queries access_codes table for exact match (maybeSingle)
   - if valid: sets validAccess = true
   - if invalid: deletes cookie, falls through
   - on error: falls through to free-tier check

3. free-tier quota (only if no valid access code)
   - counts rows in question_log where ip = client_ip
   → 403 if count >= 3
   → 503 if database query fails
```

---

## 7. error response format

errors vary by endpoint:

**standard endpoints** (`/api/books`, `/api/books/[id]`, `/api/verify-code`, `/api/music/playlists`):
```typescript
{ error: string }
// or for verify-code:
{ success: false, error: string }
```

**hooks middleware** (pre-endpoint, JSON):
```typescript
{ error: string }   // 429, 403, or 503
```

**`/api/ask`** (in-stream, SSE):
```typescript
{ type: 'error', error?: string, fallback_audio_url: string }
```

the `fallback_audio_url` is a direct supabase storage URL to a pre-recorded MP3 fallback. when the book's `voice_id` is known, per-voice fallbacks are used so the error voice matches the narrator.

---

## 8. server-side clients

`apps/web/src/lib/server/clients.ts` provides lazy-initialized singletons:

```typescript
getSupabase(): SupabaseClient
// env: SUPABASE_URL + SUPABASE_SERVICE_KEY (service role, bypasses RLS)

getOpenAI(): OpenAI
// env: OPENAI_API_KEY

getAnthropic(): Anthropic
// env: ANTHROPIC_API_KEY
```

each throws on missing env vars. the service key (not anon key) is used because the server needs to insert into `question_log` and `code_usage_log` tables that have RLS policies.

---

## 9. environment variables

| variable | required by | description |
|----------|-------------|-------------|
| `SUPABASE_URL` | all endpoints | supabase project URL |
| `SUPABASE_SERVICE_KEY` | all endpoints | supabase service role key (not anon — bypasses RLS) |
| `OPENAI_API_KEY` | `/api/ask` | whisper transcription, text-embedding-3-small, gpt-4o-mini-tts |
| `ANTHROPIC_API_KEY` | `/api/ask` | claude-sonnet-4-20250514 streaming |
| `ELEVENLABS_API_KEY` | `/api/ask` | elevenlabs TTS (optional — only needed for books with `tts_provider: "elevenlabs"`) |
| `UPSTASH_REDIS_REST_URL` | hooks middleware | upstash redis REST endpoint (optional — rate limiting disabled without it) |
| `UPSTASH_REDIS_REST_TOKEN` | hooks middleware | upstash redis auth token (optional) |
| `DEBUG_LOGGING` | `/api/ask` | set to `"true"` to enable verbose timing logs (optional) |

---

## 10. file structure
```
apps/web/src/
├── hooks.server.ts                      # rate limiting, access code validation, free-tier quota
├── routes/api/
│   ├── books/
│   │   ├── +server.ts                   # GET /api/books
│   │   └── [id]/
│   │       └── +server.ts              # GET /api/books/[id]
│   ├── ask/
│   │   └── +server.ts                  # POST /api/ask (SSE streaming)
│   ├── verify-code/
│   │   └── +server.ts                  # POST /api/verify-code
│   └── music/
│       └── playlists/
│           └── +server.ts              # GET /api/music/playlists
└── lib/server/
    ├── clients.ts                       # supabase, openai, anthropic singletons
    ├── storage.ts                       # listBooks(), getBookDetail()
    ├── book-cache.ts                    # in-memory cache (5-min TTL)
    ├── context.ts                       # getRecentChunks(), getCurrentCheckpoint()
    ├── rag.ts                           # queryRAG() — pgvector similarity search
    ├── prompts.ts                       # buildSystemPrompt(), buildUserMessage(), shouldUseRAG()
    └── tts.ts                           # generateSpeech() — openai / elevenlabs
```
