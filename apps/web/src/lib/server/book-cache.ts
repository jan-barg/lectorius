import { getBookDetail } from './storage';
import type { GetBookResponse } from '$lib/types';

interface CacheEntry {
	data: GetBookResponse;
	fetchedAt: number;
}

const cache = new Map<string, CacheEntry>();
const TTL_MS = 5 * 60 * 1000; // 5 minutes

export async function getCachedBook(bookId: string): Promise<GetBookResponse | null> {
	const cached = cache.get(bookId);

	if (cached && Date.now() - cached.fetchedAt < TTL_MS) {
		return cached.data;
	}

	try {
		const data = await getBookDetail(bookId);
		cache.set(bookId, { data, fetchedAt: Date.now() });
		return data;
	} catch {
		return null;
	}
}
