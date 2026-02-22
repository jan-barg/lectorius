import { browser } from '$app/environment';

const STORAGE_KEY = 'lectorius_reading_history';

export interface ReadingHistoryEntry {
	book_id: string;
	last_chunk_index: number;
	total_chunks: number;
	last_played: number;
}

function readAll(): Record<string, ReadingHistoryEntry> {
	if (!browser) return {};
	try {
		const raw = localStorage.getItem(STORAGE_KEY);
		return raw ? JSON.parse(raw) : {};
	} catch {
		return {};
	}
}

export function updateReadingHistory(
	bookId: string,
	chunkIndex: number,
	totalChunks: number
): void {
	if (!browser) return;
	try {
		const all = readAll();
		all[bookId] = {
			book_id: bookId,
			last_chunk_index: chunkIndex,
			total_chunks: totalChunks,
			last_played: Date.now()
		};
		localStorage.setItem(STORAGE_KEY, JSON.stringify(all));
	} catch {
		// localStorage full or unavailable
	}
}

export function getReadingHistory(): ReadingHistoryEntry[] {
	return Object.values(readAll()).sort((a, b) => b.last_played - a.last_played);
}
