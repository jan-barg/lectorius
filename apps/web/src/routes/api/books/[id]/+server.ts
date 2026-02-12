import { json, error } from '@sveltejs/kit';
import { getBookDetail } from '$lib/server/storage';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = async ({ params }) => {
	try {
		const data = await getBookDetail(params.id);
		return json(data);
	} catch (e) {
		const message = e instanceof Error ? e.message : 'Book not found';
		error(404, message);
	}
};
