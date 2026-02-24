import { json, error } from '@sveltejs/kit';
import { env } from '$env/dynamic/private';
import { getSupabase } from '$lib/server/clients';
import type { RequestHandler } from './$types';

const BUCKET = 'system';

function prettifyName(filename: string): string {
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

		const { data: folders, error: listError } = await supabase.storage
			.from(BUCKET)
			.list('music/general', { limit: 100 });

		if (listError || !folders) {
			return error(500, `Failed to list playlists: ${listError?.message}`);
		}

		const playlistFolders = folders.filter((f) => f.id === null);
		const playlists = [];

		for (const folder of playlistFolders) {
			const { data: files, error: filesError } = await supabase.storage
				.from(BUCKET)
				.list(`music/general/${folder.name}`, { limit: 100 });

			if (filesError || !files) continue;

			const songs = files
				.filter((f) => f.name.endsWith('.mp3'))
				.sort((a, b) => a.name.localeCompare(b.name))
				.map((f, i) => ({
					song_id: `${folder.name}-${i}`,
					title: prettifyName(f.name),
					duration_ms: 0,
					file_path: `${storageBase}/music/general/${folder.name}/${encodeURIComponent(f.name)}`
				}));

			if (songs.length === 0) continue;

			playlists.push({
				playlist_id: folder.name,
				name: prettifyName(folder.name),
				type: 'general' as const,
				book_id: null,
				songs
			});
		}

		return json({ playlists });
	} catch (e) {
		const message = e instanceof Error ? e.message : 'Failed to fetch playlists';
		return error(500, message);
	}
};
