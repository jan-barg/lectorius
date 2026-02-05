# lectorius — product requirements document

**version:** 1.0  
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
| web app | desktop/mobile browser, responsive design |
| push-to-talk q&a | user clicks button to ask a question |
| pre-recorded narration | elevenlabs standard voice, generated via pipeline |
| voice responses | llm answer converted to speech via elevenlabs (same voice as narrator) |
| spoiler prevention | llm and rag constrained to playhead position |
| playback controls | play/pause, skip ±30 sec, playback speed (1x/1.5x/2x), sleep timer |
| chapter navigation | free jump to any chapter |
| follow-up questions | user can ask multiple questions before resuming |
| auto-resume | playback resumes automatically after q&a |
| progress auto-save | local storage, persists across sessions |
| public domain books | 3 demo books (english, gutenberg source) |
| pre-recorded fallbacks | error/edge-case phrases stored as audio files |

### 2.2 out of scope (v2+)

| feature | notes |
|---------|-------|
| mobile native app | required for wake word / hands-free |
| wake word detection | "hey lectorius" — needs native app |
| user accounts | auth, cloud sync, multi-device |
| user-uploaded books | pipeline runs manually for now |
| highlights / notes | — |
| share quotes | — |
| dictionary lookup | — |
| multiple character voices | — |
| offline playback | q&a requires llm, narration could work offline but descoped |

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
1. user opens web app
2. user selects book from library (3 options)
3. playback begins (or resumes from saved position)
4. user listens...
5. user presses "ask" button (push-to-talk)
6. playback pauses
7. user speaks question
8. system transcribes question (whisper api)
9. system gathers context:
   - current chunk + last ~60 seconds of text
   - memory checkpoint (characters, places, plot threads)
   - rag retrieval (if needed), filtered to current playhead
10. llm generates answer (constrained: no spoilers)
11. elevenlabs generates audio from answer
12. audio streams to user
13. user can:
    a. ask follow-up → repeat from step 7
    b. stay silent → auto-resume playback after 2 seconds
14. playback resumes from paused position
```

### 3.2 edge case flows

**not enough context (early in book):**
```
user asks question in first 30 seconds
→ play pre-recorded: "i don't have enough context yet—let's keep reading."
→ auto-resume
```

**off-topic question:**
```
user asks "what's the weather tomorrow?"
→ play pre-recorded: "i can only help with questions about this book."
→ wait for follow-up or auto-resume
```

**api failure (llm or tts):**
```
llm or elevenlabs call fails after retries
→ play pre-recorded: "i can't seem to find an answer right now."
→ auto-resume
```

---

## 4. technical decisions

### 4.1 platform & hosting

| component | choice |
|-----------|--------|
| frontend | svelte (sveltekit), hosted on vercel |
| backend api | sveltekit api routes or vercel edge functions |
| database | supabase (postgres) — for future auth/sync, minimal use in mvp |
| storage | supabase storage — book pack audio files |
| llm | anthropic claude (claude-sonnet-4-20250514) |
| tts | elevenlabs (standard voice, eleven_multilingual_v2) |
| stt | whisper api |

### 4.2 voice strategy

- **narrator voice:** elevenlabs standard voice (no cloning cost)
- **assistant voice:** same voice as narrator (seamless experience)
- **fallback phrases:** pre-recorded with same voice, stored globally

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
| claude sonnet (1k in, 500 out tokens) | ~$0.005 |
| elevenlabs (100 words response) | ~$0.01-0.02 |
| **total per question** | **~$0.015-0.025** |

---

## 5. content library (mvp)

### 5.1 book selection criteria

- public domain (project gutenberg)
- english language
- well-structured chapters
- mix of fiction and non-fiction
- moderate length (not 1000+ pages)

### 5.2 proposed books

| book | author | type | why |
|------|--------|------|-----|
| the great gatsby | f. scott fitzgerald | fiction | popular, character-driven, good for q&a |
| the art of war | sun tzu | non-fiction | short chapters, factual queries |
| pride and prejudice | jane austen | fiction | complex characters, relationship questions |

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

```typescript
interface PlaybackState {
  book_id: string;
  chunk_index: number;
  chunk_time_ms: number;
  playback_speed: 1 | 1.5 | 2;
  is_playing: boolean;
  is_asking: boolean;
}
```

### 6.3 user progress (localstorage mvp)

```typescript
interface UserProgress {
  [book_id: string]: {
    chunk_index: number;
    chunk_time_ms: number;
    last_played_at: string;
  }
}
```

---

## 7. pre-recorded fallback phrases

stored in `audio/system/` (global, not per-book):

| filename | text | use case |
|----------|------|----------|
| `no_context_yet.mp3` | "i don't have enough context yet—let's keep reading." | question in first 30 sec |
| `book_only.mp3` | "i can only help with questions about this book." | off-topic question |
| `error.mp3` | "i can't seem to find an answer right now." | api failure |
| `resuming.mp3` | "let's get back to the story." | after q&a, before resume |

---

## 8. open questions

| # | question | impact | decision needed by |
|---|----------|--------|-------------------|
| 1 | stream llm→tts or wait for full response? | latency vs complexity | before api build |
| 2 | vercel blob vs supabase storage for audio? | cost, ease of use | before deployment |

---

## 9. milestones

| milestone | deliverable | target |
|-----------|-------------|--------|
| m1 | pipeline complete, 1 book processed | week 1-2 |
| m2 | basic playback working (no q&a) | week 3 |
| m3 | q&a flow working (push-to-talk → voice response) | week 4-5 |
| m4 | full mvp with 3 books, polished ui | week 6-7 |
| m5 | deployed, shareable demo | week 8 |

---

## 10. future considerations (v2)

- native mobile app with wake word
- user accounts + cloud sync
- user-uploaded books (pipeline as a service)
- monetization: subscription or per-book purchase
- rate limiting / usage caps for public deployment


