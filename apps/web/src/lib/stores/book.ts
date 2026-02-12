import { writable } from 'svelte/store';
import type { LoadedBook } from '$lib/types';
import type { BookStoreState } from './types';
import { DEFAULT_BOOK_STATE } from './types';

function createBookStore() {
	const { subscribe, set, update } = writable<BookStoreState>(DEFAULT_BOOK_STATE);

	return {
		subscribe,
		startLoading: () => update((s) => ({ ...s, is_loading: true, error: null })),
		setBook: (book: LoadedBook) =>
			set({ loaded_book: book, is_loading: false, error: null }),
		setError: (error: string) =>
			update((s) => ({ ...s, is_loading: false, error })),
		clear: () => set(DEFAULT_BOOK_STATE)
	};
}

export const book = createBookStore();
