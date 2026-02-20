import type { LoadedBook } from '$lib/types';

// =============================================================================
// playback state
// =============================================================================

export type PlaybackSpeed = 1 | 1.5 | 2;

export interface PlaybackState {
	book_id: string | null;
	chunk_index: number;
	chunk_time_ms: number;
	is_playing: boolean;
	playback_speed: PlaybackSpeed;
	volume: number;
	sleep_timer_end: number | null;
}

export const DEFAULT_PLAYBACK_STATE: PlaybackState = {
	book_id: null,
	chunk_index: 1,
	chunk_time_ms: 0,
	is_playing: false,
	playback_speed: 1,
	volume: 1,
	sleep_timer_end: null
};

// =============================================================================
// q&a state
// =============================================================================

export interface QAState {
	is_recording: boolean;
	is_processing: boolean;
	is_playing_answer: boolean;
	last_question: string | null;
	last_answer: string | null;
	error: string | null;
}

export const DEFAULT_QA_STATE: QAState = {
	is_recording: false,
	is_processing: false,
	is_playing_answer: false,
	last_question: null,
	last_answer: null,
	error: null
};

// =============================================================================
// book store state
// =============================================================================

export interface BookStoreState {
	loaded_book: LoadedBook | null;
	is_loading: boolean;
	error: string | null;
}

export const DEFAULT_BOOK_STATE: BookStoreState = {
	loaded_book: null,
	is_loading: false,
	error: null
};
