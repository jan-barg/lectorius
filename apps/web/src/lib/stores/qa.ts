import { writable } from 'svelte/store';
import type { QAState } from './types';
import { DEFAULT_QA_STATE } from './types';

function createQAStore() {
	const { subscribe, set, update } = writable<QAState>(DEFAULT_QA_STATE);

	return {
		subscribe,
		startRecording: () =>
			update((s) => ({ ...s, is_recording: true, error: null })),
		stopRecording: () =>
			update((s) => ({ ...s, is_recording: false, is_processing: true })),
		setAnswer: (question: string, answer: string) =>
			update((s) => ({
				...s,
				is_processing: false,
				is_playing_answer: true,
				last_question: question,
				last_answer: answer
			})),
		setError: (error: string) =>
			update((s) => ({ ...s, is_processing: false, is_playing_answer: false, error })),
		reset: () => set(DEFAULT_QA_STATE)
	};
}

export const qa = createQAStore();
