# Lectorius Frontend Design Specification

## 1. Typography & Colors

### Fonts
| Role | Font Family | Fallback | Why? |
| :--- | :--- | :--- | :--- |
| **UI / Headings** | **Outfit** | `sans-serif` | Modern, geometric, friendly, high readability. |
| **Body / Book Content** | **Merriweather** | `serif` | Classic serif optimized for screens, excellent for long-form reading. |

### Color Palette ("Techy-Bookish")
Supports **System / Light / Dark** modes. Single accent color across both modes: `violet-600` (#7c3aed).

#### Light Mode (Warm Paper)
| Token | Tailwind Class | Hex | Usage |
| :--- | :--- | :--- | :--- |
| Background | `bg-stone-50` | #fafaf9 | Page background |
| Surface | `bg-white` | #ffffff | Cards, panels |
| Text | `text-stone-900` | #1c1917 | Primary text |
| Muted | `text-stone-500` | #78716c | Secondary text, labels |
| Accent | `text-violet-600` | #7c3aed | Buttons, active states, progress fills |

#### Dark Mode (Deep Tech)
| Token | Tailwind Class | Hex | Usage |
| :--- | :--- | :--- | :--- |
| Background | `bg-slate-950` | #020617 | Page background |
| Surface | `bg-slate-900` | #0f172a | Cards, panels |
| Text | `text-slate-50` | #f8fafc | Primary text |
| Muted | `text-slate-400` | #94a3b8 | Secondary text, labels |
| Accent | `text-violet-600` | #7c3aed | Buttons, active states, progress fills |

#### Tailwind Config
Replace the current custom color tokens (`primary`, `secondary`, `background`, `surface`, `text`, `muted`) with the above system. Use Tailwind's `class` strategy for dark mode — apply `dark` class to `<html>`.

---

## 2. Settings

### Settings Panel
- Triggered by gear icon in the top nav bar (existing)
- Slides in from the right with backdrop overlay
- Escape key closes (existing)

### Theme Switcher
**Status: Currently inert. This spec defines the full implementation.**

| Property | Specification |
| :--- | :--- |
| **Options** | System / Light / Dark |
| **Control** | Horizontal toggle bar with three segments |
| **Active Indicator** | Sliding highlight pill that animates between options |
| **Animation** | Highlight slides with `ease-out` transition (~200ms) |
| **Persistence** | Store preference in `localStorage` (key: `lectorius_theme`) |
| **Application** | Read stored theme on app init. Apply `dark` class to `<html>` based on preference or system `prefers-color-scheme`. |
| **System Mode** | When set to "System", listen for `prefers-color-scheme` changes and apply immediately |
| **Theme Transition** | All color properties transition smoothly (`transition-colors duration-300`) on theme change |

### Settings Store
**Status: Currently a placeholder (type export only). Implement as a Svelte writable store.**

| Property | Type | Default | Persistence |
| :--- | :--- | :--- | :--- |
| `theme` | `'system' \| 'light' \| 'dark'` | `'system'` | `localStorage` key: `lectorius_theme` |

The store should sync to `localStorage` on write and hydrate from `localStorage` on init. On subscribe, apply/remove the `dark` class on `<html>`.

---

## 3. Library View

### A. Personalized Greeting
Time-based randomized greeting at the top of the library page.

| Time Window | Greetings (randomized) |
| :--- | :--- |
| **Default** (any time) | "Hello there, {name}" / "What are we reading, {name}?" / "The book worm is back!" |
| **After 10 PM** | "Fancy a lullaby, {name}?" / "Trouble sleeping, {name}?" |
| **Before Noon** | "Morning, pal." / "How's your coffee, {name}?" |

- Name is hardcoded as **"Jan"** for now (will use user accounts later)
- Greeting is selected once on page load, does not change while viewing
- Font: Outfit

### B. Layout Structure
```
[Nav bar — logo + settings gear]
[Greeting]
[TextureBar — CSS-rendered decorative divider]

— Continue Reading —
[Book cards with progress - sorted by last_played desc]

— Read Something New —
[Book cards - unread books]
```

- **TextureBar**: CSS-rendered decorative divider (see Section 3.E)
- **Continue Reading**: Only shown if user has started at least one book
- **Read Something New**: Books with no reading history - horizontally arranged, scrollable element (if many books present, too many to fit in its container)
- Section headers: Outfit font, subtle muted color

### C. Continue Reading
| Property | Specification |
| :--- | :--- |
| **Storage** | `localStorage` key: `lectorius_playback` (existing) |
| **Data Per Book** | `book_id`, `last_chunk_index`, `total_chunks`, `last_played` timestamp |
| **Display** | Book cards with progress bar overlay at bottom of cover |
| **Sort Order** | Most recently played first |
| **Progress Bar** | Thin bar at bottom of card, shows `chunk_index / total_chunks` percentage, filled in accent color |

### D. Book Card
| Property | Specification |
| :--- | :--- |
| **Aspect Ratio** | `3:4` |
| **Source** | `/books/[book-id]/cover.mp4` (Supabase `books` bucket) |
| **Default State** | Video paused at `currentTime = 0` (first frame) |
| **Hover** | Video plays. Card lifts (`-translate-y-2`) with subtle shadow increase |
| **Mouse Leave** | Pause immediately. Freeze on current frame. Does NOT reset to frame 0. |
| **Looping** | Disabled. Plays once through, stops on final frame. |
| **Ended State** | Track `ended` boolean. Once video completes one full play, it stays frozen on the final frame permanently — subsequent hovers do NOT replay. |
| **Metadata Overlay** | Title + Author over gradient overlay at bottom of cover. Glassmorphism effect (`backdrop-blur`, semi-transparent background). |
| **Progress Overlay** | For "Continue Reading" cards only: thin accent-colored bar at very bottom of cover. |
| **Fallback** | If video fails to load or no `cover.mp4` exists, show first letter of title as large centered initial. |

#### Coming Soon State
| Property | Specification |
| :--- | :--- |
| **Wrapper** | `<div>` (no link), `cursor-not-allowed` |
| **Visual** | Dimmed: `opacity-70`, `grayscale-30%` |
| **Badge** | "Coming Soon" pill, top-right, accent color background |
| **Video** | Still plays on hover |
| **Progress** | No progress overlay |

### E. TextureBar
Pure CSS decorative divider — no static image assets. Theme-aware, transitions with the rest of the app.

| Property | Specification |
| :--- | :--- |
| **Element** | Single `<div>`, no children |
| **Height** | 3px |
| **Width** | 100% of content container |
| **Gradient** | `linear-gradient(to right, transparent, violet-600, transparent)` — accent color peaks at center, fades to transparent at edges |
| **Opacity** | 50% (light mode), 40% (dark mode) — decorative, not dominant |
| **Noise Texture** | Subtle grain overlay via inline SVG filter: `<svg>` with `<feTurbulence type="fractal" baseFrequency="0.9">` + `<feColorMatrix>` applied as CSS `filter: url(#grain)` — gives a paper/tactile feel |
| **Margin** | `my-6` — comfortable spacing above and below |
| **Border Radius** | `rounded-full` — soft ends |
| **Theme Transition** | `transition-opacity duration-300` — fades smoothly on theme change |
| **Dark Mode Enhancement** | Optional subtle `box-shadow: 0 0 8px violet-600/20` glow for a "neon ink line" feel |

Implementation notes:
- The SVG filter can be defined once inline (hidden, zero-size) and referenced by ID
- Alternatively, skip the noise filter for simplicity — the gradient alone reads as a refined divider. The noise adds a paper/grain quality but is not essential.
- No external assets, no image files, fully CSS/SVG

---

## 4. Book Player View

### A. Layout Structure
```
[Back link — "← Library"]
[Book title + author — centered]
[Cover art — video, frozen on first frame, 3:4]
[Progress bar — seekable, hover tooltip]
[Playback controls — skip back, play/pause, skip forward, speed]
[Ask button — push-to-talk Q&A]
[Chapter list — scrollable, current chapter highlighted]
```

### B. Cover Art (Player)
| Property | Specification |
| :--- | :--- |
| **Aspect Ratio** | `3:4` |
| **Behavior** | Loads video, freezes on first frame (`loadeddata` → pause). Never plays on the player page. |
| **Fallback** | First letter of book title as centered initial |

### C. Progress Bar
| Property | Specification |
| :--- | :--- |
| **Track** | Full width, surface color background, rounded |
| **Fill** | Accent color, shows elapsed / total time as percentage |
| **Click** | Seekable — maps click position to chunk + offset, jumps playback |
| **Hover Tooltip** | Shows `mm:ss` time + chapter title at hovered position. Tooltip follows cursor along the bar. |
| **Time Display** | `elapsed / total` below the bar, muted color, Outfit font |
| **Animation** | Fill width transitions smoothly on seek (`transition-all duration-150`) |

### D. Playback Controls
Four buttons in a horizontal row, centered:

| Button | Icon | Size | Style | Action |
| :--- | :--- | :--- | :--- | :--- |
| **Skip Back** | ↺ 15 | Standard | Ghost / outline | Seek -15s, handles cross-chunk boundaries |
| **Play/Pause** | ▶ / ❚❚ | Large (primary) | Filled accent color, rounded-full | Toggle playback |
| **Skip Forward** | ↻ 15 | Standard | Ghost / outline | Seek +15s, handles cross-chunk boundaries |
| **Speed** | "1x" / "1.5x" / "2x" | Pill | Ghost / outline | Cycles through speeds |

All buttons:
- `active:scale-95` press feedback
- Hover: subtle lift or glow
- Play/Pause: accent background, white icon. Transitions icon with crossfade.

### E. Chapter List
| Property | Specification |
| :--- | :--- |
| **Layout** | Vertical list below controls |
| **Current Chapter** | Highlighted with accent color text + subtle accent background strip |
| **Other Chapters** | Muted text color |
| **Click** | Jumps to first chunk of that chapter, starts playback |
| **Animation** | Current chapter highlight transitions smoothly when chapter changes |
| **Font** | Merriweather (book content font) for chapter titles |

---

## 5. Ask Button & Q&A States

The Ask button is the centerpiece interaction on the Book Player page. It handles push-to-talk recording, processing, and answer playback.

### Button States

| State | Visual | Label | Animation | Interaction |
| :--- | :--- | :--- | :--- | :--- |
| **Idle** | Neutral circle. Stone-100 (light) / Slate-800 (dark) | "Hold to Ask" | None | Enabled — press & hold to record |
| **Hover / Warm-up** | Warm glow radiates outward (orange/rose `box-shadow`) | "Hold to Ask" | Glow pulse, subtle | Pre-acquires mic stream on hover (existing optimization) |
| **Recording** | Accent color (violet-600) fill | "Listening..." | Rhythmic breathing pulse (`scale` oscillation, ~1.5s cycle) | Hold to continue recording. Release to submit. |
| **Thinking** | Accent color border, neutral fill | "Thinking..." | Rotating conic-gradient border (replaces current spinner) | Disabled — no interaction |
| **Speaking** | Green fill (`emerald-500` light / `emerald-400` dark) | "Speaking..." | Gentle pulse (slower than recording, ~2.5s cycle) | Disabled — answer audio is playing |
| **Error** | Red flash, then fade back to idle | "Try again" | Brief red pulse, auto-resets after 2s | Disabled during error, then returns to idle |

### Q&A Flow (unchanged, visual states mapped)
1. **Idle** → User hovers → **Warm-up** (mic stream pre-acquired)
2. User presses & holds → **Recording** (playback pauses, mic records)
3. User releases → **Thinking** (audio sent to API, SSE stream begins)
4. First audio chunk arrives → **Speaking** (audio chunks queued and played sequentially)
5. All audio played → 2s delay → **Idle** (playback resumes)
6. On error → **Error** (fallback audio plays if available, then reset)
7. Pointer leaves during recording → Cancel, return to **Idle**

### Thinking State Detail
The rotating conic-gradient border replaces the current CSS spinner. Implementation:
- Pseudo-element or wrapper `div` with `conic-gradient(from var(--angle), violet-600, transparent, violet-600)`
- Animate `--angle` from `0deg` to `360deg` via `@keyframes` (~1.5s loop)
- Button content (text/icon) sits inside, unaffected by rotation

---

## 6. Animations

### Global
| Animation | Where | Specification |
| :--- | :--- | :--- |
| **Theme Toggle** | Entire app | `transition-colors duration-300` on all themed elements. Sliding pill on toggle control. |
| **Page Transitions** | Library ↔ Player | Subtle crossfade or slide transition |

### Micro-interactions
| Animation | Where | Specification |
| :--- | :--- | :--- |
| **Button Press** | All buttons | `active:scale-95`, `transition-transform duration-75` |
| **Hover Lift** | Book cards, buttons | `-translate-y-1` to `-translate-y-2`, subtle shadow increase |
| **Glow Effects** | Ask button hover, accented elements in dark mode | `box-shadow` with accent color at low opacity. More prominent in dark mode. |
| **Progress Fill** | Progress bar, card progress overlays | `transition-all duration-150` on width changes |
| **Chapter Highlight** | Chapter list | `transition-colors duration-200` when active chapter changes |
| **Play/Pause Icon** | Play button | Crossfade between play and pause icons (`opacity` + `scale` transition) |
| **Settings** | Settings button | Settings navigation scrolls out from the right |

---

## 7. Asset Locations

| Asset Type | Location |
| :--- | :--- |
| **Book cover videos** | `books/[book-id]/cover.mp4` (Supabase `books` bucket) |
| **App icons/graphics** | `/static/images/` |
| **Fallback audio** | `system/audio/` (Supabase `system` bucket) |
| **Fonts** | Google Fonts: Outfit, Merriweather |

Note: TextureBar is pure CSS — no static texture assets needed.

---

## 8. Component Inventory

### Existing — Redesign with new design system
| Component | File | Changes Needed |
| :--- | :--- | :--- |
| Greeting | `Greeting.svelte` | Update font to Outfit, apply theme colors |
| TextureBar | `TextureBar.svelte` | Rewrite as CSS gradient + optional SVG noise filter (see Section 3.E) |
| BookCard | `BookCard.svelte` | Glassmorphism overlay, theme colors, hover animations |
| BookCardVideo | `BookCardVideo.svelte` | Ensure `ended` state tracked (existing), no replay after completion |
| ProgressOverlay | `ProgressOverlay.svelte` | Accent color fill |
| Controls | `Controls.svelte` | Restyle buttons per spec, add press feedback |
| AskButton | `AskButton.svelte` | Full state redesign per Section 5. Replace spinner with conic gradient. Add Speaking state styling. |
| ProgressBar | `ProgressBar.svelte` | Theme colors, smooth fill transition |
| ChapterList | `ChapterList.svelte` | Merriweather font, accent highlight with transition |
| SettingsPanel | `SettingsPanel.svelte` | Theme colors, ensure slide-in works with new palette |

### Existing — Implement (currently placeholder/inert)
| Component | File | Changes Needed |
| :--- | :--- | :--- |
| ThemeSwitcher | `ThemeSwitcher.svelte` | Wire up: persist to localStorage, apply `dark` class to `<html>`, listen for system changes |
| Settings store | `settings.ts` | Implement writable store with localStorage sync |

### Existing — Remove
| Component | File | Reason |
| :--- | :--- | :--- |
| BookList | `BookList.svelte` | Unused, superseded by ContinueReading + ReadSomethingNew |

---

## 9. Future Considerations

- Book search functionality
- Book categories / genres
- User accounts + auth (replace hardcoded name, cloud sync progress)
- Bookmarks within books
- Reading history / stats dashboard
- Social features (share progress, recommendations)
- Offline mode / PWA support
- Expanded settings (playback defaults, voice preference, notification sounds)