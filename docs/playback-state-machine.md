## 1. overview

the playback state machine governs all user interactions with the audio player. it defines all possible states, valid transitions, triggering events, and side effects.

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
                                         │      ┌────────────┐
                                         └────► │ processing │
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
| `PLAY` | `playing` | start audio playback |
| `SELECT_BOOK` | `loading` | load different book |
| `SEEK_CHAPTER` | `ready` | update chunk_index, preload audio |
| `SEEK_CHUNK` | `ready` | update chunk_index, preload audio |

### playing

| event | target | actions |
|-------|--------|---------|
| `PAUSE` | `paused` | pause audio |
| `PUSH_TO_TALK_START` | `recording` | pause audio, start recording |
| `CHUNK_ENDED` | `playing` | load next chunk, continue (if more chunks) |
| `CHUNK_ENDED` | `ready` | book finished (if last chunk) |
| `SEEK_FORWARD` | `playing` | skip +30 sec |
| `SEEK_BACKWARD` | `playing` | skip -30 sec |
| `SEEK_CHAPTER` | `playing` | jump to chapter start |
| `SET_SPEED` | `playing` | change playback rate |
| `SLEEP_TIMER_FIRED` | `paused` | pause playback, clear timer |
| `AUDIO_ERROR` | `error` | store error |

### paused

| event | target | actions |
|-------|--------|---------|
| `PLAY` | `playing` | resume playback |
| `PUSH_TO_TALK_START` | `recording` | start recording |
| `SEEK_FORWARD` | `paused` | skip +30 sec |
| `SEEK_BACKWARD` | `paused` | skip -30 sec |
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

| event | target | actions |
|-------|--------|---------|
| `ASK_SUCCESS` | `answering` | store answer, play audio |
| `ASK_ERROR` | `answering` | play fallback audio (if available) |
| `ASK_ERROR` | `error` | store error (if no fallback) |

### answering

| event | target | actions |
|-------|--------|---------|
| `ANSWER_COMPLETE` | `playing` | auto-resume after 2s silence |
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
| `RECORDING_CANCEL` | user cancels recording | — |
| `SEEK_FORWARD` | user clicks +30s | — |
| `SEEK_BACKWARD` | user clicks -30s | — |
| `SEEK_CHAPTER` | user selects chapter | `{ chapter_index }` |
| `SET_SPEED` | user changes speed | `{ speed: 1 \| 1.5 \| 2 }` |
| `SET_SLEEP_TIMER` | user sets timer | `{ minutes \| null }` |
| `DISMISS_ERROR` | user dismisses error | — |

### system events

| event | trigger | payload |
|-------|---------|---------|
| `LOAD_SUCCESS` | api returns book data | `{ book: LoadedBook }` |
| `LOAD_ERROR` | api call fails | `{ error }` |
| `CHUNK_ENDED` | audio element `ended` event | — |
| `ASK_SUCCESS` | api returns answer | `{ question_text, answer_text, answer_audio }` |
| `ASK_ERROR` | api call fails | `{ error, fallback_audio_id? }` |
| `ANSWER_COMPLETE` | answer audio ends + 2s timeout | — |
| `AUDIO_ERROR` | audio element `error` event | `{ error }` |
| `RECORDING_ERROR` | mediarecorder fails | `{ error }` |
| `SLEEP_TIMER_FIRED` | timer expires | — |

---

## 6. key behaviors

### seeking (±30 seconds)

- walk forward/backward through chunks based on `duration_ms` from playback map
- clamp to book boundaries (chunk 1 start, last chunk end)

### progress persistence

- save to localstorage every 5 seconds while playing
- save on pause, chunk change, and page unload
- restore on book load

### sleep timer

- check every second if `Date.now() >= sleep_timer_end`
- fire `SLEEP_TIMER_FIRED` to pause playback

### auto-resume after answer

- when answer audio ends, wait 2 seconds
- if still in `answering` state (no follow-up started), transition to `playing`

### preloading

- when chunk starts playing, preload next chunk audio
- enables near-gapless playback