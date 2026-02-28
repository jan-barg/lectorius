# lectorius — system architecture

**version:** 1.5
**status:** draft
**last updated:** february 2026

---

## 1. architecture overview

```
CLIENT (Browser)
    │
    │  SvelteKit SPA
    │  - Audio Player + Music Player
    │  - Playback State
    │  - Q&A (push-to-talk → SSE stream)
    │  - Library + Settings
    │
    ▼
VERCEL
    │
    │  SvelteKit API Routes
    │  - GET /api/books
    │  - GET /api/books/[id]
    │  - POST /api/ask (SSE streaming)
    │  - POST /api/verify-code
    │  - GET /api/music/playlists
    │
    │  Hooks Middleware (POST /api/ask only)
    │  - Upstash Redis rate limiting
    │  - Access code validation
    │  - Free-tier IP quota
    │
    ├───────────────────────────────────┐
    │                                   │
    ▼                                   ▼
EXTERNAL APIs                      SUPABASE
    │                                   │
    ├─ OpenAI                          ├─ Storage
    │    - Whisper (STT)               │    - Book packs (audio, metadata)
    │    - text-embedding-3-small      │    - System audio (fallbacks, music)
    │    - gpt-4o-mini-tts (TTS)       │    - Per-voice fallback audio
    ├─ Anthropic Claude (LLM)          │
    └─ ElevenLabs (TTS, per-book)      └─ Database (Postgres + pgvector)
                                            - book_embeddings (vector search)
UPSTASH REDIS                               - access_codes
    └─ Rate limiting (60 req/hr)            - question_log
                                            - code_usage_log
                                            - playlists
```

---

## 2. components

### 2.1 client (sveltekit spa)

runs entirely in the browser.

| component | responsibility |
|-----------|----------------|
| audio engine | `AudioEngine` class wrapping two `HTMLAudioElement`s (primary + preload). loads chunk audio from supabase storage URLs, handles playback, speed, volume, seeking. preloads next chunk. |
| music audio engine | `MusicAudioEngine` class for background music. supports `fadeTo()` for audio ducking during Q&A. |
| recorder | `Recorder` class using `MediaRecorder` API. multi-phase warm-up for near-instant push-to-talk (see section 7.2). |
| playback store | svelte store managing current position, play/pause, speed, volume. persists per-book positions to localstorage. |
| q&a (ask button) | `AskButton.svelte`: push-to-talk flow with SSE streaming — record audio → send to api → receive sentence-by-sentence audio via SSE → play sequentially. handles access code prompts on free-tier limit. |
| library | library page with book cards (video covers), continue reading / read something new sections, welcome card for first-time users, time-of-day greeting. |
| player | orchestrator component: owns `AudioEngine` + `Recorder`, subscribes to stores, manages playback lifecycle, saves position periodically. |
| music player | global component (persists across routes): playlist selector, now-playing bar, play/pause, volume, sync-with-book toggle, audio ducking during Q&A. |
| settings panel | slide-in panel: name editing, theme switching (system/light/dark), access code entry, reading history management. |

key client-side data (in memory after book load):

```typescript
interface LoadedBook {
  book: BookMeta;
  chapters: Chapter[];
  chunks: Chunk[];
  playbackMap: PlaybackMapEntry[];
  checkpoints: MemoryCheckpoint[];
  cover_video_url: string | null;
}
```

### 2.2 api routes (vercel functions)

stateless serverless functions. all heavy lifting (llm, tts) happens here. audio files are served directly from supabase storage public URLs (no proxy endpoint).

| route | method | purpose |
|-------|--------|---------|
| `/api/books` | GET | list available books (5-min module-level cache) |
| `/api/books/[id]` | GET | get full book pack metadata (chapters, chunks, playback map, checkpoints) |
| `/api/ask` | POST | main q&a endpoint: stt → context → llm → streaming tts. returns SSE. gated by hooks middleware. |
| `/api/verify-code` | POST | validate access code, set httpOnly cookie (30-day expiry) |
| `/api/music/playlists` | GET | list playlists and songs from supabase storage (5-min cache header) |

### 2.3 external services

| service | purpose | model / api |
|---------|---------|-------------|
| openai whisper | speech-to-text | `whisper-1` |
| openai embeddings | question embedding for RAG | `text-embedding-3-small` |
| openai tts | text-to-speech (default / fallback) | `gpt-4o-mini-tts`, voice `nova` |
| anthropic claude | answer generation (streaming) | `claude-sonnet-4-20250514`, max 500 tokens |
| elevenlabs tts | text-to-speech (per-book, production) | `eleven_flash_v2_5` (low latency for live Q&A) |
| upstash redis | rate limiting | sliding window, 60 req/hr |

### 2.4 supabase

| component | usage |
|-----------|-------|
| storage (`books` bucket) | book pack files: audio chunks, metadata, video covers |
| storage (`system` bucket) | fallback audio (generic + per-voice), music files |
| database: `book_embeddings` | postgres + pgvector: vector similarity search via `match_embeddings` RPC |
| database: `access_codes` | access code validation for authenticated users |
| database: `question_log` | question logging (ip, user_name, book_id, question). also used for free-tier IP quota counting |
| database: `code_usage_log` | tracks access code usage (code, ip, user_name) |
| database: `playlists` | music playlist metadata (name, type, book_id, folder_path) |

---

## 3. data flow

### 3.1 book loading

```
1. user selects book from library
2. client: GET /api/books/{id}
3. api: fetch from supabase storage:
   - book.json
   - chapters.jsonl
   - chunks.jsonl
   - playback_map.jsonl
   - memory/checkpoints.jsonl
4. api: parse, return as json
5. client: store in memory, initialize playback state
6. client: begin loading first chunk audio
```

### 3.2 playback

```
1. client: read playback_map to get audio url for current chunk
2. client: fetch audio from supabase storage
3. client: play audio via html5 audio element
4. client: on chunk end, increment chunk_index, preload next chunk
5. client: update localstorage progress periodically
```

### 3.3 q&a flow (SSE streaming)

```
1. user holds "ask" button
2. client: duck music volume (fade to 0), pause audiobook, start recording
3. user releases button
4. client: convert blob to base64, POST /api/ask { book_id, chunk_index, audio_base64 }
   - hooks middleware intercepts:
     a. rate limit check (upstash redis, 60/hr) → 429 if exceeded
     b. access code cookie validation → set validAccess flag
     c. free-tier IP quota (3 questions) → 403 if exceeded
5. api: validate inputs (audio size ≤ 5MB, book_id non-empty, chunk_index ≥ 1)
6. api: load book data from in-memory cache (5-min TTL)
7. api: transcribe audio via whisper → question_text
8. api: guard: reject if chunk_index < 5 (not enough context)
9. api: assemble context
   - recent chunks around playhead (last ~60 sec of audio)
   - latest memory checkpoint ≤ chunk_index
   - if shouldUseRAG(question): pgvector similarity search (filtered to ≤ chunk_index)
10. api: begin SSE stream
    - send { type: 'question', text: question_text }
    - stream claude response, extract sentences as they complete
    - for each sentence: generate TTS audio → send { type: 'audio', text, audio (base64) }
    - send { type: 'done', full_answer }
11. client: receive SSE events, queue audio chunks, play sequentially
12. client: when stream done + audio queue empty → wait 2s → resume playback, unduck music
```

TTS provider selection: uses the book's `tts_provider` (openai or elevenlabs). if the book's provider fails, falls back to openai.

### 3.4 error flow

```
1. hooks error (rate limit, access code, free tier):
   - 429: client shows "too many questions" error
   - 403 "Free limit reached": client shows inline access code prompt
   - 503: client shows "service unavailable" error

2. api error (whisper, claude, or tts failure):
   - api: send SSE { type: 'error', fallback_audio_url } with per-voice fallback URL
   - client: play pre-recorded fallback from supabase storage (per-voice if available, generic otherwise)
   - client: auto-resume playback
```

---

## 4. storage structure (supabase)

```
supabase-storage/
├── books/                              # book packs bucket
│   └── {book_id}/
│       ├── manifest.json
│       ├── book.json
│       ├── chapters.jsonl
│       ├── chunks.jsonl
│       ├── playback_map.jsonl
│       ├── cover.mp4                   # video cover for library cards
│       ├── audio/
│       │   └── chunks/
│       │       └── {chunk_id}.mp3
│       └── memory/
│           └── checkpoints.jsonl
└── system/                             # system assets bucket
    ├── audio/                          # generic fallback audio (OpenAI "alloy" voice)
    │   ├── no_context_yet.mp3
    │   ├── book_only.mp3
    │   └── error.mp3
    ├── fallback-audio/                 # per-voice fallback audio
    │   └── {voice_id}/
    │       ├── no_context_yet.mp3
    │       ├── error.mp3
    │       └── book_only.mp3
    └── music/                          # background music files
        └── {folder_path}/
            └── *.mp3
```

note: `rag/` directory (FAISS index, meta.jsonl) exists in local pipeline output only — not uploaded to supabase. embeddings live in the `book_embeddings` postgres table (pgvector).

---

## 5. api route details

### 5.1 GET /api/books

```json
{
  "books": [
    {
      "book_id": "pride-and-prejudice",
      "title": "Pride and Prejudice",
      "author": "Jane Austen",
      "cover_url": "https://...",
      "cover_video_url": "https://.../cover.mp4",
      "total_chapters": 24,
      "total_chunks": 1847,
      "total_duration_ms": 3542000,
      "status": "available"
    }
  ]
}
```

response is cached at the module level for 5 minutes.

### 5.2 GET /api/books/[id]

```json
{
  "book": {
    "book_id": "...", "title": "...", "author": "...", "language": "en",
    "book_type": "fiction", "tts_provider": "elevenlabs", "voice_id": "..."
  },
  "chapters": [{ "chapter_id": "...", "index": 1, "title": "...", "char_start": 0, "char_end": 24531 }],
  "chunks": [{ "chunk_id": "...", "chapter_id": "...", "chunk_index": 1, "text": "...", "char_start": 0, "char_end": 587 }],
  "playback_map": [{ "chunk_id": "...", "audio_path": "https://...full-url.mp3", "duration_ms": 4523, "chunk_index": 1 }],
  "checkpoints": [{ "until_chunk_index": 50, "summary": "...", "entities": {} }],
  "cover_video_url": "https://.../cover.mp4"
}
```

audio paths in `playback_map` are rewritten from relative paths to full supabase storage public URLs.

### 5.3 POST /api/ask (SSE)

gated by hooks middleware (see section 8).

**request** (`application/json`):
```json
{
  "book_id": "string",
  "chunk_index": "number (integer ≥ 1)",
  "audio_base64": "string (base64-encoded webm, max 5MB)"
}
```

**response** (`text/event-stream`):
```
data: {"type":"question","text":"Who is Mr. Darcy?"}

data: {"type":"audio","text":"Mr. Darcy is a wealthy gentleman...","audio":"base64..."}

data: {"type":"audio","text":"He first appears at the Meryton ball.","audio":"base64..."}

data: {"type":"done","full_answer":"Mr. Darcy is a wealthy gentleman... He first appears at the Meryton ball."}
```

**error event:**
```
data: {"type":"error","error":"Transcription failed","fallback_audio_url":"https://.../error.mp3"}
```

fallback URLs resolve to per-voice audio (`system/fallback-audio/{voice_id}/{id}.mp3`) when the book has a `voice_id`, otherwise generic (`system/audio/{id}.mp3`).

### 5.4 POST /api/verify-code

**request:**
```json
{ "code": "string", "user_name": "string (optional)" }
```

**response (success):** `{ "success": true }` + sets `lectorius_access` httpOnly cookie (30-day, secure, sameSite lax)

**response (error):** `{ "error": "Invalid access code" }` (401)

### 5.5 GET /api/music/playlists

```json
{
  "playlists": [
    {
      "playlist_id": "...",
      "name": "Classical Reading",
      "type": "general",
      "book_id": null,
      "songs": [
        { "title": "Moonlight Sonata", "file_url": "https://...", "duration_ms": null }
      ]
    }
  ]
}
```

song titles are prettified from filenames (strip numbers/prefixes, title-case). response has `Cache-Control: public, max-age=300`.

---

## 6. client state management

### 6.1 stores (svelte)

all stores use svelte writable pattern, exposing methods rather than raw `set`/`update`.

```typescript
// stores/playback.ts
interface PlaybackState {
  book_id: string | null;
  chunk_index: number;
  chunk_time_ms: number;
  is_playing: boolean;
  playback_speed: 1 | 1.5 | 2;
  volume: number;              // 0-1 float
  sleep_timer_end: number | null;
}

// stores/qa.ts
interface QAState {
  is_recording: boolean;
  is_processing: boolean;
  is_playing_answer: boolean;
  last_question: string | null;
  last_answer: string | null;
  error: string | null;
}

// stores/book.ts
interface BookStoreState {
  loaded_book: LoadedBook | null;
  is_loading: boolean;
  error: string | null;
}

// stores/music.ts
interface MusicState {
  current_playlist_id: string | null;
  current_song_index: number;
  current_time: number;
  volume: number;
  loop: boolean;
  is_playing: boolean;
  ducked: boolean;             // faded during Q&A
  sync_with_book: boolean;     // play/pause with audiobook
}

// stores/settings.ts — theme: 'system' | 'light' | 'dark'
// stores/user.ts — user display name (string)
// stores/reading-history.ts — plain functions, not a svelte store
```

### 6.2 localstorage schema

```typescript
// key: "lectorius_playback"
// per-book positions keyed by book_id
interface SavedPositions {
  [book_id: string]: {
    chunk_index: number;
    chunk_time_ms: number;
  }
}

// key: "lectorius_theme"
// value: "system" | "light" | "dark"

// key: "lectorius_user"
// value: display name string (set from WelcomeCard on first visit)

// key: "lectorius_music"
// persisted subset of MusicState (excludes is_playing and ducked — always start false)
interface SavedMusic {
  current_playlist_id: string | null;
  current_song_index: number;
  current_time: number;
  volume: number;
  loop: boolean;
  sync_with_book: boolean;
}

// key: "lectorius_reading_history"
// per-book reading progress for continue reading section
interface ReadingHistoryEntry {
  book_id: string;
  last_chunk_index: number;
  total_chunks: number;
  last_played: number;         // timestamp
}
```

sessionStorage: `lectorius_music_prompts_shown` — array of playlist IDs for which the book music prompt was already shown this session.

---

## 7. audio handling

### 7.1 audiobook playback (`AudioEngine`)

`$lib/services/audio.ts` — wraps two `HTMLAudioElement`s (primary + preload secondary).

**playback map:** stored as `Map<number, PlaybackMapEntry>` for O(1) chunk lookups. audio URLs point directly to supabase storage public URLs (rewritten from relative paths during book load).

**preloading:**
- on chunk start, preload next chunk audio into secondary element
- `play()` sets src + optional seek, then starts playback and triggers preload

**volume:** applies `toPerceptualVolume(volume * 100)` (quadratic curve) for natural-feeling volume control.

**speed control:** html5 audio `playbackRate` property (1, 1.5, 2).

**callbacks:** `onChunkEnd` (triggers `nextChunk()` in player), `onTimeUpdate(ms)` (updates playback store).

### 7.1.1 music playback (`MusicAudioEngine`)

`$lib/services/music-audio.ts` — similar pattern for background music.

- `fadeTo(targetVolume, durationMs)` for audio ducking during Q&A (16ms interval-based linear interpolation)
- `preload()` for next song
- callbacks: `onTimeUpdate(seconds)`, `onSongEnd()`, `onDurationKnown(durationMs)`
- music player syncs play/pause with audiobook when `sync_with_book` is enabled

### 7.2 recording (push-to-talk)

the recorder (`$lib/services/recorder.ts`) uses the mediarecorder api with a multi-phase warm-up strategy to eliminate latency on button press.

**the problem:** calling `getUserMedia()` + creating a `MediaRecorder` on button press adds ~1-1.5s of delay before recording actually starts. the user presses the button and nothing happens for over a second.

**the solution:** a 3-phase warm-up pipeline that front-loads the expensive work.

#### phase 1: stream pre-acquisition (on first play)

when the user presses play for the first time, `Player.svelte` calls `recorder.acquireStream()`. this satisfies the browser's user-gesture requirement for mic permissions and stores the `MediaStream` for reuse across multiple recordings.

```
user presses play → Player calls recorder.acquireStream()
                     └── getUserMedia() → stores this.stream
                         (browser shows mic permission prompt if needed)
```

the stream is kept alive between recordings. `stopRecording()` only cleans up the `MediaRecorder`, not the stream. `releaseStream()` is called on page destroy.

#### phase 2: warm-up on hover (on mouseenter / touchstart)

when the user hovers over (or touches) the ask button, `AskButton.svelte` calls `recorder.warmUp()`. this is fire-and-forget:

```
user hovers ask button → AskButton calls recorder.warmUp()
                          ├── if stream dead: getUserMedia() → stores this.stream
                          └── new MediaRecorder(stream) → stores this.warmRecorder
```

if the user leaves without clicking, `recorder.releaseWarmStream()` stops the tracks and nulls both stream and warm recorder.

#### phase 3: instant start (on pointerdown)

when the user presses the ask button, `startRecording()` checks for a warm recorder:

```
user presses ask → AskButton calls recorder.startRecording()
                    ├── warm path: move this.warmRecorder → this.mediaRecorder, call .start()
                    │   (~1-5ms, near-instant)
                    │
                    └── cold fallback: getUserMedia() + new MediaRecorder() + .start()
                        (~800-1500ms, only if warm-up didn't happen)
```

#### recorder lifecycle

```
                    acquireStream()          warmUp()            startRecording()
                    (first play)             (hover)             (press)
                         │                      │                     │
                         ▼                      ▼                     ▼
                    ┌─────────┐          ┌─────────────┐       ┌───────────┐
                    │ stream  │ ──reuse→ │ stream +    │ ─move→│ recording │
                    │ alive   │          │ warmRecorder│       │ active    │
                    └─────────┘          └─────────────┘       └───────────┘
                                               │                     │
                                          mouseleave            stopRecording()
                                               │                     │
                                               ▼                     ▼
                                        releaseWarmStream()    blob returned
                                        (stops tracks)         (stream kept alive)
```

#### recording format

- format: `audio/webm;codecs=opus`
- output: `Blob` converted to base64 via `blobToBase64()` (FileReader API)
- sent to server as `audio_base64` field in POST /api/ask json body
- server decodes base64 → buffer → openai `toFile()` → whisper api

#### edge cases

| scenario | behavior |
|----------|----------|
| stream dies between recordings | `isStreamAlive()` checks track `readyState === 'live'`; falls back to `getUserMedia()` |
| hover without clicking | `releaseWarmStream()` on pointerleave stops tracks |
| pointer leaves during recording | `cancelRecording()` stops recorder, keeps stream alive |
| page destroy / navigation | `releaseStream()` stops all tracks, nulls everything |
| mic permission denied | caught in `handlePointerDown()`, sets qa error state |
| warm-up fails silently | `warmUp()` is fire-and-forget; `startRecording()` falls back to cold path |
| concurrent warm-up calls | `isWarming` flag prevents race conditions |

#### file ownership

| file | role |
|------|------|
| `$lib/services/recorder.ts` | `Recorder` class: stream lifecycle, mediarecorder management, blob output |
| `$lib/components/qa/AskButton.svelte` | ui component: hover warm-up, press-to-record, release-to-send |
| `$lib/components/player/Player.svelte` | owns the `Recorder` instance, calls `acquireStream()` on first play, `releaseStream()` on destroy |

---

## 8. security and access control

### 8.1 hooks middleware (`hooks.server.ts`)

intercepts only `POST /api/ask`. all other routes pass through unguarded.

three-layer guard (evaluated in order):

1. **rate limiting** — upstash redis sliding window (60 req/hr)
   - identifier: access code cookie if present, otherwise `ip:{clientIP}`
   - fails open: if redis is unavailable, rate limiting is skipped (doesn't block users)
   - returns 429 `{ error: "Too many questions. Try again later." }`

2. **access code validation** — checks `lectorius_access` cookie against `access_codes` table
   - valid: sets `validAccess = true`, skips free-tier check
   - invalid: deletes the cookie, falls through to free-tier check
   - db failure: falls through to free-tier check

3. **free-tier IP quota** — counts rows in `question_log` matching client IP
   - limit: 3 questions per IP (lifetime, not resetting)
   - returns 403 `{ error: "Free limit reached" }`
   - db failure: returns 503

### 8.2 general security

| concern | mitigation |
|---------|------------|
| api key exposure | all external api calls happen server-side only (`$lib/server/` modules) |
| supabase storage access | public read for book audio (no sensitive data). server uses service key (not anon) for db writes |
| input validation | `audio_base64` ≤ 5MB, `book_id` non-empty string, `chunk_index` integer ≥ 1, `access code` string ≤ 100 chars |
| cookie security | `lectorius_access`: httpOnly, secure (in prod), sameSite lax, 30-day expiry |
| client IP | uses `event.getClientAddress()` (sveltekit built-in, handles proxies) |
| user name | trimmed and capped to 100 chars from `X-User-Name` header |

---

## 9. environment variables

```bash
# supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=xxx              # service role key (bypasses RLS for inserts)

# openai (whisper STT, embeddings, TTS fallback)
OPENAI_API_KEY=xxx

# anthropic (claude LLM)
ANTHROPIC_API_KEY=xxx

# elevenlabs (per-book TTS)
ELEVENLABS_API_KEY=xxx

# rate limiting (upstash redis)
UPSTASH_REDIS_REST_URL=xxx            # optional — rate limiting disabled if missing
UPSTASH_REDIS_REST_TOKEN=xxx

# debugging
DEBUG_LOGGING=true                    # verbose timing logs in /api/ask
```

note: `SUPABASE_ANON_KEY` is not used — the web app uses the service key for all server-side operations (needed to bypass RLS for inserts into `question_log` and `code_usage_log`). `ELEVENLABS_VOICE_ID` is not used by the web app — voice IDs come from each book's `book.json`.

---

## 10. deployment

### 10.1 pipeline (manual)

installed as `lectorius-pipeline` CLI (python ≥ 3.11, `pip install -e ./pipeline`).

```bash
# full pipeline (ingest → chapterize → chunkify → validate)
lectorius-pipeline process \
  --input ./source/pride-and-prejudice.epub \
  --book-id pride-and-prejudice \
  --output-dir ./books/pride-and-prejudice \
  --tts-provider elevenlabs --voice-id <voice_id>

# individual stages
lectorius-pipeline tts --book-dir ./books/pride-and-prejudice
lectorius-pipeline rag --book-dir ./books/pride-and-prejudice
lectorius-pipeline memory --book-dir ./books/pride-and-prejudice

# per-voice fallback audio
lectorius-pipeline generate-fallbacks --book-dir ./books/pride-and-prejudice

# upload to supabase storage
# (manual — upload books/{book_id}/ contents to supabase books bucket)
```

### 10.2 web app (vercel)

- adapter: `@sveltejs/adapter-auto` (auto-detects vercel)
- connect repo to vercel
- set environment variables in dashboard
- push to main → auto-deploy
- api routes become vercel serverless functions

---

## 11. future architecture changes

| change | trigger | impact |
|--------|---------|--------|
| full user accounts | beyond access codes | supabase auth, user profiles, progress sync to db |
| server-side progress sync | multi-device support | progress table in postgres, sync on book load |
| native mobile app | wake word requirement | separate react native / flutter codebase |
| pipeline as service | user uploads | queue system, background jobs |

**already implemented (previously listed as future):**
- ~~streaming tts~~ — implemented via SSE: sentence-by-sentence TTS as claude streams tokens
- ~~access control~~ — implemented via access codes + free-tier IP quota (not full user accounts, but functional auth)
