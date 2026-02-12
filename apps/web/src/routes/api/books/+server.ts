import { json, error } from '@sveltejs/kit';
import { listBooks } from '$lib/server/storage';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = async () => {
	try {
		const books = await listBooks();
		return json({ books });
	} catch (e) {
		const message = e instanceof Error ? e.message : 'Failed to list books';
		error(500, message);
	}
};
