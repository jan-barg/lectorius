import { json, error } from '@sveltejs/kit';
import { env } from '$env/dynamic/private';
import { getSupabase } from '$lib/server/clients';
import type { RequestHandler } from './$types';

const BUCKET = 'system';

function prettifyTitle(filename: string): string {
	return filename
		.replace(/\.mp3$/i, '')
		.replace(/^\d+[-_]?\s*/, '')
		.replace(/[-_]/g, ' ')
		.replace(/\b\w/g, (c) => c.toUpperCase())
		.trim();
}

export const GET: RequestHandler = async () => {
	try {
		const supabase = getSupabase();
		const storageBase = `${env.SUPABASE_URL}/storage/v1/object/public/${BUCKET}`;

		const { data: rows, error: dbError } = await supabase
			.from('playlists')
			.select('playlist_id, name, type, book_id, folder_path');

		if (dbError || !rows) {
			return error(500, `Failed to query playlists: ${dbError?.message}`);
		}

		const playlists = [];

		for (const row of rows) {
			const { data: files, error: filesError } = await supabase.storage
				.from(BUCKET)
				.list(row.folder_path, { limit: 200 });

			if (filesError || !files) continue;

			const songs = files
				.filter((f) => f.name.endsWith('.mp3'))
				.sort((a, b) => a.name.localeCompare(b.name))
				.map((f) => ({
					title: prettifyTitle(f.name),
					file_url: `${storageBase}/${row.folder_path}/${encodeURIComponent(f.name)}`
				}));

			if (songs.length === 0) continue;

			playlists.push({
				playlist_id: row.playlist_id,
				name: row.name,
				type: row.type,
				book_id: row.book_id,
				songs
			});
		}

		return json({ playlists });
	} catch (e) {
		const message = e instanceof Error ? e.message : 'Failed to fetch playlists';
		return error(500, message);
	}
};
