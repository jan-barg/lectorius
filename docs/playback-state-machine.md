# lectorius — playback state machine specification

**version:** 1.1
**status:** draft
**last updated:** february 2026

---

## 1. overview

the playback state machine governs all user interactions with the audio player. it defines all possible states, valid transitions, triggering events, and side effects.

the implementation uses **distributed reactive stores** rather than a single unified state machine. playback state (`is_playing`, `chunk_index`, `speed`, `volume`), q&a state (`is_recording`, `is_processing`, `is_playing_answer`), and book state (`loaded_book`, `is_loading`) live in separate svelte stores that coordinate through reactive subscriptions. the state diagram below is a conceptual model — the code achieves equivalent behavior through store composition.

---

## 2. states

| state | description |
|-------|-------------|
| `idle` | no book loaded. initial state. |
| `loading` | book metadata loading from api. |
| `ready` | book loaded, playback paused, ready to play. |
| `playing` | audio actively playing. |
| `paused` | playback paused by user. |
| `recording` | user is recording a question (push-to-talk active). |
| `processing` | question sent to api, waiting for response. |
| `answering` | playing the assistant's voice response. |
| `error` | recoverable error occurred. |

**note:** the `sleep_timer_end` field is defined in the `PlaybackState` type but has no implementation — no methods update it and no timer checks it. sleep timer is a planned feature.

---

## 3. state diagram
```
                          select book
              ┌───────┐ ──────────────► ┌─────────┐
              │ idle  │                 │ loading │
              └───────┘ ◄────┐          └────┬────┘
                  ▲          │               │
                  │     dismiss error        ├── success ──► ready
                  │          │               │
              ┌───┴───┐      │               └── error ────► error
              │ error │ ◄────┴───────────────────────────────────┐
              └───────┘                                          │
                                                                 │
              ┌───────┐ ◄── play ─── ┌───────┐ ◄── pause ─── ┌───┴─────┐
              │ ready │              │ paused │               │ playing │
              └───────┘              └────┬───┘               └────┬────┘
                                         │                        │
                                         │   push-to-talk start   │
                                         └────────────┬───────────┘
                                                      ▼
                                                ┌───────────┐
                                         ┌───── │ recording │ ◄──── follow-up
                                         │      └─────┬─────┘
                                         │            │
                                    cancel            │ release
                                         │            ▼
                                         ▼      ┌────────────┐
                                       paused   │ processing │
                                                └──────┬─────┘
                                                       │
                                          success/error with fallback
                                                       ▼
                                                ┌───────────┐
                                                │ answering │
                                                └─────┬─────┘
                                                      │
                                               answer complete
                                                      │
                                                      ▼
                                              auto-resume to playing
```

---

## 4. state transitions

### idle

| event | target | actions |
|-------|--------|---------|
| `SELECT_BOOK` | `loading` | start loading book metadata |

### loading

| event | target | actions |
|-------|--------|---------|
| `LOAD_SUCCESS` | `ready` | store book data, restore saved progress |
| `LOAD_ERROR` | `error` | store error message |

### ready

| event | target | actions |
|-------|--------|---------|
| `PLAY` | `playing` | start audio playback, acquire mic stream (first play only) |
| `SELECT_BOOK` | `loading` | load different book |
| `SEEK_CHAPTER` | `ready` | update chunk_index, preload audio |

### playing

| event | target | actions |
|-------|--------|---------|
| `PAUSE` | `paused` | pause audio |
| `PUSH_TO_TALK_START` | `recording` | pause audio, duck music, start recording |
| `CHUNK_ENDED` | `playing` | load next chunk, continue (if more chunks) |
| `CHUNK_ENDED` | `paused` | book finished (if last chunk) |
| `SEEK_FORWARD` | `playing` | skip +15 sec |
| `SEEK_BACKWARD` | `playing` | skip -15 sec |
| `SEEK_CHAPTER` | `playing` | jump to chapter start |
| `SET_SPEED` | `playing` | change playback rate |
| `AUDIO_ERROR` | `error` | store error |

### paused

| event | target | actions |
|-------|--------|---------|
| `PLAY` | `playing` | resume playback |
| `PUSH_TO_TALK_START` | `recording` | duck music, start recording |
| `SEEK_FORWARD` | `paused` | skip +15 sec |
| `SEEK_BACKWARD` | `paused` | skip -15 sec |
| `SEEK_CHAPTER` | `paused` | jump to chapter |
| `SET_SPEED` | `paused` | change playback rate |
| `SELECT_BOOK` | `loading` | load different book |

### recording

| event | target | actions |
|-------|--------|---------|
| `PUSH_TO_TALK_END` | `processing` | send audio to api |
| `RECORDING_CANCEL` | `paused` | discard recording |
| `RECORDING_ERROR` | `error` | store error |

### processing

the api returns an SSE stream. the first `audio` event triggers the transition to `answering` — subsequent audio events are queued and played sequentially.

| event | target | actions |
|-------|--------|---------|
| `ASK_SUCCESS` | `answering` | play first audio chunk, queue remaining |
| `ASK_ERROR` | `answering` | play fallback audio (if available) |
| `ASK_ERROR` | `error` | store error (if no fallback) |
| `ASK_LIMIT_REACHED` | `paused` | show access code prompt (free-tier 3-question limit) |

### answering

| event | target | actions |
|-------|--------|---------|
| `ANSWER_COMPLETE` | `playing` | auto-resume after 2s delay, unduck music |
| `PUSH_TO_TALK_START` | `recording` | stop answer, start new recording (follow-up) |
| `PLAY` | `playing` | stop answer, resume book manually |

### error

| event | target | actions |
|-------|--------|---------|
| `DISMISS_ERROR` | `ready` | clear error (if book loaded) |
| `DISMISS_ERROR` | `idle` | clear error (if no book) |
| `SELECT_BOOK` | `loading` | load book |

---

## 5. events

### user events

| event | trigger | payload |
|-------|---------|---------|
| `SELECT_BOOK` | user clicks book in library | `{ book_id }` |
| `PLAY` | user clicks play | — |
| `PAUSE` | user clicks pause | — |
| `PUSH_TO_TALK_START` | user presses ask button | — |
| `PUSH_TO_TALK_END` | user releases ask button | `{ audio: Blob }` |
| `RECORDING_CANCEL` | user leaves ask button while recording | — |
| `SEEK_FORWARD` | user clicks +15s | — |
| `SEEK_BACKWARD` | user clicks -15s | — |
| `SEEK_CHAPTER` | user selects chapter | `{ chapter_index }` |
| `SET_SPEED` | user cycles speed button | `{ speed: 1 \| 1.5 \| 2 }` |
| `DISMISS_ERROR` | user dismisses error | — |

### system events

| event | trigger | payload |
|-------|---------|---------|
| `LOAD_SUCCESS` | api returns book data | `{ book: LoadedBook }` |
| `LOAD_ERROR` | api call fails | `{ error }` |
| `CHUNK_ENDED` | audio element `ended` event | — |
| `ASK_SUCCESS` | first SSE `audio` event received | `{ question_text, audio_base64 }` |
| `ASK_ERROR` | SSE `error` event or fetch failure | `{ error, fallback_audio_url? }` |
| `ANSWER_COMPLETE` | audio queue empty + stream done + 2s delay | — |
| `AUDIO_ERROR` | audio element `error` event | `{ error }` |
| `RECORDING_ERROR` | mediarecorder fails | `{ error }` |

### SSE stream events (server → client)

the `/api/ask` endpoint returns a server-sent events stream with these event types:

| type | payload | description |
|------|---------|-------------|
| `question` | `{ text }` | transcribed question text |
| `audio` | `{ text, audio }` | sentence-by-sentence TTS (base64 mp3) |
| `done` | `{ full_answer }` | stream complete, full answer text |
| `error` | `{ error, fallback_audio_url? }` | error with optional fallback audio URL |

---

## 6. key behaviors

### seeking (±15 seconds)

- walk forward/backward through chunks based on `duration_ms` from playback map
- if skip crosses a chunk boundary, jump to next/previous chunk and seek to the calculated offset
- clamp to book boundaries (chunk 1 start, last chunk end)

### progress bar seeking

- click/drag on progress bar calculates target position from percentage of total duration
- linear search through sorted playback map to find target chunk and offset within that chunk
- fires `onSeek(chunkIndex, offsetMs)` callback to player

### progress persistence

- save to localstorage every 5 seconds while playing
- save on pause, chunk change, and page unload (`beforeunload`)
- restore on book load (saved offset applied on first `play()` call)
- also persists reading history separately: `{ book_id, last_chunk_index, total_chunks, last_played }`

### auto-resume after answer

- when answer audio queue empties AND stream is done, wait 2 seconds
- if no follow-up recording started during the delay, transition to `playing` and unduck music

### preloading

- when chunk starts playing, preload next chunk's audio via a separate `Audio` element
- previous preload is released before loading next
- enables near-gapless playback

### recorder warmup

- mic stream acquired once on first play button press (browser requires user gesture)
- stream is reused for all recordings — not released between questions
- on ask button hover, `warmUp()` pre-initializes a `MediaRecorder` with the existing stream
- `isWarming` flag prevents race condition if hover triggers multiple warmups
- result: near-instant recording start on push-to-talk

### music ducking

- background music volume is reduced when recording or answering
- `music.duck()` on recording start, `music.unduck()` on answer complete or cancel
- music player observes `ducked` state reactively

### audio queue (SSE answer playback)

- each SSE `audio` event pushes a base64 mp3 chunk to `audioQueue`
- `playNextAudio()` plays from queue sequentially — each `onended` chains to next
- on error in a single audio chunk, skip to next in queue (don't break the chain)
- `checkComplete()` fires after queue empties AND stream is done → triggers auto-resume delay

### action lock

- `actionLock` flag on ask button prevents race conditions from rapid clicks
- while locked, pointer events are ignored
- released in `finally` block to ensure cleanup on errors

### free-tier quota

- on 403 "Free limit reached" from `/api/ask`, recording/processing state is cleared
- access code prompt is shown to the user
- book playback is not auto-resumed (user must enter code or dismiss)