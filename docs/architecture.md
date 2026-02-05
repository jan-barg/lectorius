# lectorius — system architecture

**version:** 1.2  
**status:** draft  
**last updated:** february 2026

---

## 1. architecture overview

```
CLIENT (Browser)
    │
    │  SvelteKit SPA
    │  - Audio Player
    │  - Playback State
    │  - Q&A Manager
    │  - UI Components
    │
    ▼
VERCEL
    │
    │  SvelteKit API Routes
    │  - GET /api/books
    │  - GET /api/books/[id]
    │  - POST /api/ask
    │
    ├───────────────────────────────────┐
    │                                   │
    ▼                                   ▼
EXTERNAL APIs                      SUPABASE
    │                                   │
    ├─ OpenAI Whisper (STT)            ├─ Storage
    ├─ Anthropic Claude (LLM)          │    - Book Packs
    └─ ElevenLabs (TTS)                │    - System audio
                                       │
                                       └─ Database (future)
                                            - User auth
                                            - Progress sync
```

---

## 2. components

### 2.1 client (sveltekit spa)

runs entirely in the browser.

| component | responsibility |
|-----------|----------------|
| audio player | html5 audio element wrapper. loads chunk audio, handles playback, speed control, seeking. |
| playback state | svelte store managing current position, play/pause, speed, sleep timer. persists to localstorage. |
| q&a manager | handles push-to-talk flow: record audio → send to api → receive response → play tts audio. |
| book loader | fetches book pack metadata on book select. holds chunks, playback map, chapters in memory. |
| ui components | library view, player view, chapter list, controls, ask button. |

key client-side data (in memory after book load):

```typescript
interface LoadedBook {
  book: BookMeta;
  chapters: Chapter[];
  chunks: Chunk[];
  playbackMap: PlaybackMapEntry[];
  memoryCheckpoints: MemoryCheckpoint[];
}
```

### 2.2 api routes (vercel functions)

stateless serverless functions. all heavy lifting (llm, tts) happens here.

| route | method | purpose |
|-------|--------|---------|
| `/api/books` | GET | list available books |
| `/api/books/[id]` | GET | get book pack metadata |
| `/api/books/[id]/audio/[chunk_id]` | GET | proxy/redirect to supabase storage |
| `/api/ask` | POST | main q&a endpoint: stt → context → llm → tts → return audio |

### 2.3 external services

| service | purpose | api |
|---------|---------|-----|
| openai whisper | speech-to-text | `POST /v1/audio/transcriptions` |
| anthropic claude | answer generation | `POST /v1/messages` |
| elevenlabs | text-to-speech | `POST /v1/text-to-speech/{voice_id}` |

### 2.4 supabase

| component | usage |
|-----------|-------|
| storage | book pack files: audio chunks, metadata, system fallback audio |
| database | mvp: none. future: user accounts, progress sync |

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

### 3.3 q&a flow

```
1. user presses "ask" button
2. client: pause playback, record audio via mediarecorder api
3. user releases button
4. client: POST /api/ask { book_id, chunk_index, audio }
5. api: transcribe audio via whisper → question_text
6. api: assemble context
   - chunks around playhead (last ~60 sec)
   - latest memory checkpoint ≤ chunk_index
   - rag query (filtered to chunk_index) if needed
7. api: call claude with system prompt + context + question → answer_text
8. api: call elevenlabs tts → answer_audio (mp3 bytes)
9. api: return { question_text, answer_text, answer_audio }
10. client: play answer_audio
11. client: wait for follow-up or auto-resume after 2 sec
```

### 3.4 error flow

```
1. any api failure (whisper, claude, elevenlabs) after retries
2. api: return error response with fallback_audio_id
3. client: play pre-recorded fallback from supabase storage
4. client: auto-resume playback
```

---

## 4. storage structure (supabase)

```
supabase-storage/
├── books/
│   └── {book_id}/
│       ├── manifest.json
│       ├── book.json
│       ├── chapters.jsonl
│       ├── chunks.jsonl
│       ├── playback_map.jsonl
│       ├── audio/
│       │   └── chunks/
│       │       └── {chunk_id}.mp3
│       ├── rag/
│       │   ├── index.faiss
│       │   └── meta.jsonl
│       └── memory/
│           └── checkpoints.jsonl
└── system/
    └── audio/
        ├── no_context_yet.mp3
        ├── book_only.mp3
        ├── error.mp3
        └── resuming.mp3
```

---

## 5. api route details

### 5.1 GET /api/books

```json
{
  "books": [
    {
      "book_id": "great-gatsby",
      "title": "The Great Gatsby",
      "author": "F. Scott Fitzgerald",
      "cover_url": "https://...",
      "total_chapters": 9,
      "total_duration_ms": 18000000
    }
  ]
}
```

### 5.2 GET /api/books/[id]

```json
{
  "book": { "book_id": "...", "title": "...", "author": "...", "language": "en" },
  "chapters": [{ "chapter_id": "...", "index": 1, "title": "...", "char_start": 0, "char_end": 24531 }],
  "chunks": [{ "chunk_id": "...", "chapter_id": "...", "chunk_index": 1, "text": "...", "char_start": 0, "char_end": 587 }],
  "playback_map": [{ "chunk_id": "...", "audio_url": "...", "duration_ms": 4523 }],
  "checkpoints": [{ "until_chunk_index": 50, "summary": "...", "entities": {} }]
}
```

### 5.3 POST /api/ask

**request:**
```json
{
  "book_id": "string",
  "chunk_index": "number",
  "chunk_time_ms": "number",
  "audio": "Blob (webm or wav)"
}
```

**response (success):**
```json
{
  "success": true,
  "question_text": "string",
  "answer_text": "string",
  "answer_audio": "string (base64)"
}
```

**response (error):**
```json
{
  "success": false,
  "error": "string",
  "fallback_audio_id": "error | book_only | no_context_yet"
}
```

---

## 6. client state management

### 6.1 stores (svelte)

```typescript
// stores/playback.ts
interface PlaybackStore {
  book_id: string | null;
  chunk_index: number;
  chunk_time_ms: number;
  is_playing: boolean;
  playback_speed: 1 | 1.5 | 2;
  sleep_timer_end: number | null;
}

// stores/qa.ts
interface QAStore {
  is_recording: boolean;
  is_processing: boolean;
  is_playing_answer: boolean;
  last_question: string | null;
  last_answer: string | null;
}

// stores/book.ts
interface BookStore {
  loaded_book: LoadedBook | null;
  is_loading: boolean;
  error: string | null;
}
```

### 6.2 localstorage schema

```typescript
// key: "lectorius_progress"
interface StoredProgress {
  [book_id: string]: {
    chunk_index: number;
    chunk_time_ms: number;
    last_played_at: string;
  }
}

// key: "lectorius_settings"
interface StoredSettings {
  playback_speed: 1 | 1.5 | 2;
  volume: number;
}
```

---

## 7. audio handling

### 7.1 playback strategy

**preloading:**
- on chunk start, preload next chunk audio
- keep current + next chunk in memory
- discard chunks more than 2 behind playhead

**gapless playback:**
- mvp: accept small gap between chunks
- future: use two audio elements or web audio api

**speed control:**
- html5 audio `playbackRate` property (1, 1.5, 2)

### 7.2 recording (push-to-talk)

```javascript
const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });

recorder.ondataavailable = (e) => chunks.push(e.data);
recorder.onstop = () => {
  const blob = new Blob(chunks, { type: 'audio/webm' });
  sendToAPI(blob);
};

recorder.start();  // on button press
recorder.stop();   // on button release
```

---

## 8. security considerations (mvp)

| concern | mitigation |
|---------|------------|
| api key exposure | all external api calls happen server-side only |
| supabase storage access | public read for book audio (no sensitive data) |
| rate limiting | vercel built-in limits + custom limiting on /api/ask |
| input validation | validate book_id, chunk_index bounds server-side |

---

## 9. environment variables

```bash
# supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=xxx
SUPABASE_SERVICE_KEY=xxx

# openai (whisper)
OPENAI_API_KEY=xxx

# anthropic (claude)
ANTHROPIC_API_KEY=xxx

# elevenlabs
ELEVENLABS_API_KEY=xxx
ELEVENLABS_VOICE_ID=xxx
```

---

## 10. deployment

### 10.1 pipeline (manual)

```bash
cd pipeline
python -m lectorius_pipeline process \
  --input ./source/great-gatsby.epub \
  --book-id great-gatsby \
  --output-dir ./output/great-gatsby

# upload to supabase
supabase storage cp -r ./output/great-gatsby storage://books/great-gatsby
```

### 10.2 web app (vercel)

- connect repo to vercel
- set environment variables in dashboard
- push to main → auto-deploy

---

## 11. future architecture changes (v2)

| change | trigger | impact |
|--------|---------|--------|
| add supabase auth | user accounts needed | add auth middleware, progress table |
| move rag to server | faiss too large for client | new `/api/rag/query` endpoint |
| streaming tts | latency requirements tighten | websocket or sse for audio chunks |
| native mobile app | wake word requirement | separate react native / flutter codebase |
| pipeline as service | user uploads | queue system, background jobs |
