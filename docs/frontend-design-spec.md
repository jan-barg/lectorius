# Lectorius Frontend Design Specification

## 1. Typography & Colors

### Fonts
| Role | Font Family | Fallback | Why? |
| :--- | :--- | :--- | :--- |
| **UI / Headings** | **Outfit** | `sans-serif` | Modern, geometric, friendly, high readability. |
| **Body / Book Content** | **Merriweather** | `serif` | Classic serif optimized for screens, excellent for long-form reading. |
| **Code / Technical** | **JetBrains Mono** | `monospace` | Clean, distinct for data values or AI "thinking" logs. |

### Color Palette ("Techy-Bookish")
Supports **System / Light / Dark** modes.

#### Light Mode (Warm Paper)
- **Background**: `bg-stone-50` (#fafaf9) - Warm, paper-like.
- **Surface**: `bg-white` (#ffffff) - Clean cards.
- **Text**: `text-stone-900` (#1c1917) - Soft black ink.
- **Accent**: `violet-600` (#7c3aed) - Vibrant tech contrast.

#### Dark Mode (Deep Tech)
- **Background**: `bg-slate-950` (#020617) - Deep void blue/black.
- **Surface**: `bg-slate-900` (#0f172a) - Slightly lighter for cards.
- **Text**: `text-slate-50` (#f8fafc) - High contrast white.
- **Accent**: `violet-500` (#8b5cf6) - Glowing energy.

---

## 2. Settings

### Settings Panel
- Accessible from a sidebar or top bar icon (gear icon)
- Slides in from the right or drops down from top bar

### Theme Switcher
| Property | Specification |
| :--- | :--- |
| **Options** | System / Light / Dark |
| **Control** | Horizontal toggle bar with three segments |
| **Active Indicator** | Sliding highlight pill that animates between options |
| **Animation** | Highlight slides with `ease-out` transition (~200ms) |
| **Theme Transition** | All color properties transition smoothly (`transition-colors duration-300`) |
| **System Changes** | When set to "System", OS theme changes also animate smoothly |
| **Persistence** | Store preference in `localStorage` (key: `lectorius_theme`) |

Implementation: Apply `dark` class to `<html>` element. Tailwind dark mode uses `class` strategy.

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

### B. Layout Structure
```
[Greeting]
[Decorative horizontal texture graphic]

— Continue Reading —
[Book cards with progress - books user has started]

— Read Something New —
[Book cards - unread books]
```

- **Texture Bar**: Decorative horizontal graphic element separating greeting from content
- **Continue Reading**: Only shown if user has started at least one book
- **Read Something New**: Books with no reading history
- Section headers use the UI font (Outfit), styled as subtle dividers

### C. Continue Reading
Track books the user has listened to. Uses `localStorage` for now, user accounts later.

| Property | Specification |
| :--- | :--- |
| **Storage** | `localStorage` key: `lectorius_playback` (existing) |
| **Data Per Book** | `book_id`, `last_chunk_index`, `total_chunks`, `last_played` timestamp |
| **Display** | Book cards with progress bar overlay at bottom of cover |
| **Sort Order** | Most recently played first |
| **Progress Bar** | Thin bar at bottom of card, shows `chunk_index / total_chunks` percentage |

### D. Book Card — Video Cover Behavior
| Property | Specification |
| :--- | :--- |
| **Aspect Ratio** | `3:4` |
| **Source** | `/books/[book-id]/cover.mp4` (Supabase storage) |
| **Default State** | Video paused at `currentTime = 0` (first frame) |
| **Hover** | Video plays, ease-in to 1.0x speed. Card lifts (`-translate-y-2`) |
| **Near End** | Ease-out deceleration (like Apple Live Photos) |
| **Mouse Leave** | Pause immediately. **Does NOT reset to frame 0.** Freezes on current frame |
| **Looping** | **Disabled.** Plays once through, stops on final frame (cinemagraph style) |
| **Metadata** | Title/Author over gradient overlay at bottom. Glassmorphism effect |
| **Progress Overlay** | For "Continue Reading" cards: thin progress bar at very bottom of cover |

---

## 4. Core Components & Interactions

### A. Mic Input (Book Detail View)
*Note: This component belongs on the individual **Book Page**, not the global home page.*

| State | Visuals | Animation |
| :--- | :--- | :--- |
| **Idle** | Neutral circle (Stone-100 / Slate-800). | **Hover**: "Auto-warm" effect. A warm orange/rose glow radiates outward. |
| **Recording** | Active accent color (Violet-600/500). | **Pulse**: Rhythmic breathing animation to indicate active listening. |
| **Thinking** | Processing state. | **Sine Wave**: A rotating colorful border (conic gradient) depicting "AI processing". |

---

## 5. High-Fidelity Animations ("Nice Ass Animations")

### Global Transitions
- **Theme Toggle**: Colors fade smoothly when switching (`transition-colors duration-300`). Sliding pill highlight on the toggle bar.
- **Page Transitions**: Subtle crossfade/slide to maintain immersion.

### Micro-interactions
- **Buttons**: `active:scale-95` (Feedback on click).
- **Hover Lifts**: Cards and interactive elements float up slightly on hover.
- **Glows**: Use `box-shadow` with colored transparency to create "neon" effects in Dark Mode.
- **Video Covers**: Ease-in playback on hover, ease-out deceleration near end.

---

## 6. Asset Locations

| Asset Type | Location |
| :--- | :--- |
| **Book cover videos** | `/books/[book-id]/cover.mp4` (Supabase storage, `books` bucket) |
| **Decorative textures** | `/static/textures/` (local) or `system/textures/` (Supabase) |
| **App icons/graphics** | `/static/images/` |
| **Fallback audio** | `system/audio/` (Supabase storage) |

---

## 7. Future Considerations

- Book search functionality
- Book categories / genres
- User accounts, auth, login
- Cloud sync for reading progress
- Bookmarks within books
- Reading history / stats
- Social features (share progress, recommendations)
- Offline mode / PWA support
