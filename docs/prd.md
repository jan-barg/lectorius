# lectorius — product requirements document

**version:** 1.1
**status:** draft
**last updated:** february 2026

---

## 1. overview

### 1.1 what is lectorius?

lectorius is an interactive audiobook application that reads books aloud and answers user questions about the content in real-time. unlike traditional audiobooks, users can interrupt playback to ask questions like "who is this character?" or "when did they meet?" and receive context-aware answers grounded in what they've heard so far—never spoilers.

### 1.2 target users

- **commuters** — listening while driving or on public transit
- **casual readers** — enjoying fiction before bed or during chores
- **avid readers & history buffs** — engaging deeply with non-fiction and historical texts

### 1.3 core value proposition

"an audiobook that knows what you're listening to and can answer your questions without spoiling the story."

---

## 2. mvp scope

### 2.1 in scope

| feature | description |
|---------|-------------|
| web app | desktop/mobile browser, responsive design, dark/light/system theme |
| push-to-talk q&a | user holds button to ask a question, with recorder warmup on hover |
| per-book narration | per-book TTS provider (openai or elevenlabs), generated via pipeline |
| voice responses | llm answer streamed sentence-by-sentence through TTS (same voice as narrator) |
| spoiler prevention | llm and rag constrained to playhead position |
| playback controls | play/pause, skip ±15 sec, playback speed (1x/1.5x/2x), volume |
| chapter navigation | free jump to any chapter, progress bar seeking |
| follow-up questions | user can ask multiple questions before resuming |
| auto-resume | playback resumes automatically 2s after q&a |
| progress auto-save | localstorage, persists across sessions, plus reading history |
| public domain books | 4 available books (english, gutenberg source) |
| per-voice fallback audio | error/edge-case phrases in the book's narrator voice |
| background music | book-themed playlists, volume control, sync with audiobook, ducking during q&a |
| access control | access codes for unlimited q&a, 3-question free tier per IP |
| rate limiting | upstash redis sliding window (60 questions/hour), graceful fallback |

### 2.2 out of scope (v2+)

| feature | notes |
|---------|-------|
| mobile native app | required for wake word / hands-free |
| wake word detection | "hey lectorius" — needs native app |
| user accounts | full auth, cloud sync, multi-device (access codes exist but no accounts) |
| user-uploaded books | pipeline runs manually for now |
| highlights / notes | — |
| share quotes | — |
| multiple character voices | — |
| offline playback | q&a requires llm, narration could work offline but descoped |
| sleep timer | field defined in types but unimplemented |
| session memory | remember q&a history for follow-up context |

### 2.3 mvp success criteria

1. user can select a book and start listening
2. user can interrupt via push-to-talk and ask a question
3. system responds with accurate, spoiler-free, voice answer within 5 seconds
4. user can ask follow-up questions
5. playback auto-resumes after q&a
6. progress persists across browser sessions

---

## 3. user flows

### 3.1 primary flow: listen & ask

```
1. user opens web app → sees greeting + library
2. first visit: welcome card asks for name (optional, stored in localstorage)
3. user selects book from library (4 available books)
4. playback begins (or resumes from saved position)
5. user listens...
6. user holds "ask" button (push-to-talk)
   - playback pauses, background music ducks
   - recorder starts (pre-warmed on hover for near-instant start)
7. user speaks question, releases button
8. system transcribes question (whisper api)
9. system gathers context:
   - current chunk + last ~60 seconds of text
   - memory checkpoint (characters, places, plot threads)
   - rag retrieval (if needed), filtered to current playhead
10. llm generates answer (constrained: no spoilers)
11. answer streams sentence-by-sentence:
    - each sentence → TTS → base64 mp3 → SSE event → client audio queue
    - first sentence plays while remaining sentences are still generating
12. user can:
    a. ask follow-up → repeat from step 6
    b. stay silent → auto-resume playback after 2 seconds
13. playback resumes from paused position, music unducks
```

### 3.2 edge case flows

**not enough context (early in book):**
```
user asks question before chunk 5
→ play per-voice fallback: "i don't have enough context yet—let's keep reading."
→ auto-resume
```

**off-topic question:**
```
user asks "what's the weather tomorrow?"
→ llm responds: "i can only help with questions about this book."
→ response converted to speech normally
→ wait for follow-up or auto-resume
```

**api failure (llm or tts):**
```
llm or tts call fails
→ play per-voice fallback: "i can't seem to find an answer right now."
→ auto-resume
```

**free-tier limit reached:**
```
user without access code asks 4th question
→ 403 response, show access code prompt
→ user enters code → unlimited access (60/hr rate limit)
→ user dismisses → can continue listening but not ask more questions
```

**rate limit exceeded:**
```
authenticated user exceeds 60 questions/hour
→ 429 response: "too many questions"
→ auto-resume
```

---

## 4. technical decisions

### 4.1 platform & hosting

| component | choice |
|-----------|--------|
| frontend | svelte (sveltekit), hosted on vercel |
| backend api | sveltekit api routes (server-side) |
| database | supabase (postgres) — access codes, question log, code usage log, playlists |
| storage | supabase storage — book packs, per-voice fallback audio, music files |
| llm | anthropic claude (claude-sonnet-4-20250514) |
| tts (narration) | per-book: openai (gpt-4o-mini-tts) or elevenlabs (eleven_multilingual_v2) |
| tts (q&a) | matches book's narrator voice; elevenlabs uses eleven_flash_v2_5 for low latency |
| stt | openai whisper-1 |
| rate limiting | upstash redis (sliding window, 60/hr) |
| music | elevenlabs music, served from supabase storage |

### 4.2 voice strategy

- **narrator voice:** per-book TTS provider and voice_id configured in `book.json`
- **assistant voice:** same provider and voice as narrator (seamless experience)
- **fallback phrases:** pre-recorded per voice, stored at `system/fallback-audio/{voice_id}/`

### 4.3 latency budget

| phase | target |
|-------|--------|
| speech recognition | <1 sec |
| context assembly | <200 ms |
| llm response | 1-3 sec to first token |
| tts generation | 1-2 sec to first audio |
| **total time to voice** | **2-5 seconds** |

### 4.4 cost estimate (per question)

| service | cost |
|---------|------|
| whisper-1 transcription (~5 sec audio) | ~$0.001 |
| claude sonnet (~2k in, 500 out tokens) | ~$0.01 |
| elevenlabs tts (100 words response) | ~$0.01-0.02 |
| **total per question** | **~$0.02-0.03** |

---

## 5. content library (mvp)

### 5.1 book selection criteria

- public domain (project gutenberg)
- english language
- well-structured chapters
- mix of fiction and non-fiction
- moderate length (not 1000+ pages)

### 5.2 book catalog

| book | author | type | tts provider | status |
|------|--------|------|-------------|--------|
| pride and prejudice | jane austen | fiction | openai (nova) | available |
| a christmas carol | charles dickens | fiction | elevenlabs | available |
| the metamorphosis | franz kafka | fiction | openai (alloy) | available |
| rip van winkle | washington irving | fiction | elevenlabs | available |
| the yellow wallpaper | charlotte perkins gilman | fiction | elevenlabs | coming soon |
| the great gatsby | f. scott fitzgerald | fiction | elevenlabs | coming soon |

---

## 6. data model summary

### 6.1 book pack (pipeline output)

```
books/{book_id}/
├── manifest.json
├── book.json
├── chapters.jsonl
├── chunks.jsonl
├── playback_map.jsonl
├── audio/chunks/*.mp3
├── rag/
└── memory/checkpoints.jsonl
```

### 6.2 runtime state (client-side)

state is distributed across three svelte stores:

```typescript
// playback store
interface PlaybackState {
  book_id: string | null;
  chunk_index: number;
  chunk_time_ms: number;
  is_playing: boolean;
  playback_speed: 1 | 1.5 | 2;
  volume: number;
  sleep_timer_end: number | null;  // defined but unimplemented
}

// q&a store
interface QAState {
  is_recording: boolean;
  is_processing: boolean;
  is_playing_answer: boolean;
  last_question: string | null;
  last_answer: string | null;
  error: string | null;
}

// book store
interface BookStoreState {
  loaded_book: LoadedBook | null;
  is_loading: boolean;
  error: string | null;
}
```

### 6.3 client-side persistence (localstorage)

| key | content |
|-----|---------|
| `lectorius_playback` | `{ [book_id]: { chunk_index, chunk_time_ms } }` |
| `lectorius_history` | `{ [book_id]: { book_id, last_chunk_index, total_chunks, last_played } }` |
| `lectorius_user` | user's display name |
| `lectorius_theme` | `"system"` \| `"light"` \| `"dark"` |
| `lectorius_music` | music player state (volume, playlist, loop, sync) |

---

## 7. fallback audio

per-voice fallback audio is stored in supabase storage at `system/fallback-audio/{voice_id}/`. books sharing the same `voice_id` share fallback files. generic fallbacks (openai "alloy" voice) exist at `system/audio/` as a final fallback.

| filename | text | use case |
|----------|------|----------|
| `no_context_yet.mp3` | "i don't have enough context yet. let's keep reading." | question before chunk 5 |
| `error.mp3` | "i can't seem to find an answer right now." | api/tts failure |
| `book_only.mp3` | "i can only help with questions about this book." | off-topic (not currently served — off-topic handled by llm) |

**note:** off-topic refusal is handled entirely by the llm via system prompt constraints, not by pre-recorded audio. the `book_only` fallback exists in storage but is not served by the api — available as a future optimization if server-side off-topic detection is added.

---

## 8. resolved questions

| # | question | decision |
|---|----------|----------|
| 1 | stream llm→tts or wait for full response? | **stream.** sentence-by-sentence SSE: llm streams → extract sentences → tts each → push to client. shipped. |
| 2 | vercel blob vs supabase storage for audio? | **supabase storage.** all audio (books, music, fallbacks) served from supabase `books` and `system` buckets. |

---

## 9. milestones

| milestone | deliverable | status |
|-----------|-------------|--------|
| m1 | pipeline complete, 1 book processed | done |
| m2 | basic playback working (no q&a) | done |
| m3 | q&a flow working (push-to-talk → voice response) | done |
| m4 | full mvp with 4 books, polished ui | done |
| m5 | deployed, shareable demo | done |
| m6 | access codes, rate limiting, background music | done |
| m7 | per-voice fallback audio, elevenlabs pipeline integration | done |

---

## 10. future considerations (v2)

- native mobile app with wake word
- user accounts + cloud sync
- user-uploaded books (pipeline as a service)
- monetization: subscription or per-book purchase
- sleep timer
- session memory (remember q&a history for follow-ups)
- server-side off-topic filter (save llm cost)
- spoiler mode (user opt-in to allow future knowledge)
- confidence scoring (flag uncertain answers)
