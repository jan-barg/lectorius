import { writable } from 'svelte/store';
import type { PlaybackSpeed, PlaybackState } from './types';
import { DEFAULT_PLAYBACK_STATE } from './types';

function createPlaybackStore() {
	const { subscribe, set, update } = writable<PlaybackState>(DEFAULT_PLAYBACK_STATE);

	return {
		subscribe,
		play: () => update((s) => ({ ...s, is_playing: true })),
		pause: () => update((s) => ({ ...s, is_playing: false })),
		setChunk: (index: number) => update((s) => ({ ...s, chunk_index: index, chunk_time_ms: 0 })),
		setChunkTime: (ms: number) => update((s) => ({ ...s, chunk_time_ms: ms })),
		setSpeed: (speed: PlaybackSpeed) => update((s) => ({ ...s, playback_speed: speed })),
		setBook: (book_id: string) =>
			update((s) => ({ ...s, book_id, chunk_index: 1, chunk_time_ms: 0, is_playing: false })),
		reset: () => set(DEFAULT_PLAYBACK_STATE)
	};
}

export const playback = createPlaybackStore();
