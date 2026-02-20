import { writable, get } from 'svelte/store';
import type { PlaybackSpeed, PlaybackState } from './types';
import { DEFAULT_PLAYBACK_STATE } from './types';

const STORAGE_KEY = 'lectorius_playback';

interface BookPosition {
	chunk_index: number;
	chunk_time_ms: number;
}

type SavedPositions = Record<string, BookPosition>;

function createPlaybackStore() {
	const { subscribe, set, update } = writable<PlaybackState>(DEFAULT_PLAYBACK_STATE);

	return {
		subscribe,
		play: () => update((s) => ({ ...s, is_playing: true })),
		pause: () => update((s) => ({ ...s, is_playing: false })),
		setChunk: (index: number) => update((s) => ({ ...s, chunk_index: index, chunk_time_ms: 0 })),
		setChunkTime: (ms: number) => update((s) => ({ ...s, chunk_time_ms: ms })),
		setSpeed: (speed: PlaybackSpeed) => update((s) => ({ ...s, playback_speed: speed })),
		setVolume: (volume: number) => update((s) => ({ ...s, volume: Math.max(0, Math.min(1, volume)) })),
		setBook: (book_id: string) =>
			update((s) => ({ ...s, book_id, chunk_index: 1, chunk_time_ms: 0, is_playing: false })),
		nextChunk: (totalChunks: number) =>
			update((s) => {
				if (s.chunk_index >= totalChunks) return { ...s, is_playing: false };
				return { ...s, chunk_index: s.chunk_index + 1, chunk_time_ms: 0 };
			}),
		prevChunk: () =>
			update((s) => {
				if (s.chunk_index <= 1) return { ...s, chunk_time_ms: 0 };
				return { ...s, chunk_index: s.chunk_index - 1, chunk_time_ms: 0 };
			}),
		reset: () => set(DEFAULT_PLAYBACK_STATE)
	};
}

export const playback = createPlaybackStore();

function isBookPosition(value: unknown): value is BookPosition {
	return (
		typeof value === 'object' &&
		value !== null &&
		'chunk_index' in value &&
		'chunk_time_ms' in value
	);
}

function readPositions(): SavedPositions {
	try {
		const raw = localStorage.getItem(STORAGE_KEY);
		if (!raw) return {};
		const parsed = JSON.parse(raw) as Record<string, unknown>;
		// Filter to only valid per-book position entries (strip legacy top-level fields)
		const cleaned: SavedPositions = {};
		for (const [key, value] of Object.entries(parsed)) {
			if (isBookPosition(value)) {
				cleaned[key] = value;
			}
		}
		return cleaned;
	} catch {
		return {};
	}
}

export function savePosition(): void {
	const state = get(playback);
	if (!state.book_id) return;
	try {
		const positions = readPositions();
		positions[state.book_id] = {
			chunk_index: state.chunk_index,
			chunk_time_ms: state.chunk_time_ms
		};
		localStorage.setItem(STORAGE_KEY, JSON.stringify(positions));
	} catch {
		// localStorage full or unavailable
	}
}

export function loadSavedPosition(
	bookId: string
): { chunk_index: number; chunk_time_ms: number } | null {
	const positions = readPositions();
	return positions[bookId] ?? null;
}
