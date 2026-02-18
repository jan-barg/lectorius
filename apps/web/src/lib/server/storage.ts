import { env } from '$env/dynamic/private';
import { getSupabase } from '$lib/server/clients';
import type {
	BookMeta,
	Manifest,
	Chapter,
	Chunk,
	PlaybackMapEntry,
	MemoryCheckpoint,
	BookListItem,
	GetBookResponse
} from '$lib/types';

const BUCKET = 'books';

function parseJsonl<T>(text: string): T[] {
	return text
		.trim()
		.split('\n')
		.filter(Boolean)
		.map((line) => JSON.parse(line) as T);
}

async function downloadJson<T>(path: string): Promise<T> {
	const { data, error } = await getSupabase().storage.from(BUCKET).download(path);
	if (error || !data) {
		throw new Error(`Failed to download ${path}: ${error?.message}`);
	}
	const text = await data.text();
	return JSON.parse(text) as T;
}

async function downloadJsonl<T>(path: string): Promise<T[]> {
	const { data, error } = await getSupabase().storage.from(BUCKET).download(path);
	if (error || !data) {
		throw new Error(`Failed to download ${path}: ${error?.message}`);
	}
	const text = await data.text();
	return parseJsonl<T>(text);
}

async function downloadJsonlSafe<T>(path: string): Promise<T[]> {
	try {
		return await downloadJsonl<T>(path);
	} catch {
		return [];
	}
}

export async function listBooks(): Promise<BookListItem[]> {
	const { data: items, error } = await getSupabase().storage.from(BUCKET).list('', { limit: 100 });
	if (error || !items) {
		throw new Error(`Failed to list books: ${error?.message}`);
	}

	const folders = items.filter((item) => item.id === null);
	const results = await Promise.allSettled(
		folders.map(async (folder): Promise<BookListItem> => {
			const [bookMeta, manifest] = await Promise.all([
				downloadJson<BookMeta>(`${folder.name}/book.json`),
				downloadJson<Manifest>(`${folder.name}/manifest.json`)
			]);
			const storageBase = `${env.SUPABASE_URL}/storage/v1/object/public/${BUCKET}`;
			return {
				book_id: bookMeta.book_id,
				title: bookMeta.title,
				author: bookMeta.author,
				cover_url: null,
				cover_video_url: `${storageBase}/${bookMeta.book_id}/cover.mp4`,
				total_chapters: manifest.stats.chapters,
				total_chunks: manifest.stats.chunks,
				total_duration_ms: manifest.stats.total_audio_duration_ms
			};
		})
	);

	return results
		.filter((r): r is PromiseFulfilledResult<BookListItem> => r.status === 'fulfilled')
		.map((r) => r.value);
}

export async function getBookDetail(bookId: string): Promise<GetBookResponse> {
	const [book, chapters, chunks, playbackMapRaw, checkpoints] = await Promise.all([
		downloadJson<BookMeta>(`${bookId}/book.json`),
		downloadJsonl<Chapter>(`${bookId}/chapters.jsonl`),
		downloadJsonl<Chunk>(`${bookId}/chunks.jsonl`),
		downloadJsonl<PlaybackMapEntry>(`${bookId}/playback_map.jsonl`),
		downloadJsonlSafe<MemoryCheckpoint>(`${bookId}/memory/checkpoints.jsonl`)
	]);

	const storageBase = `${env.SUPABASE_URL}/storage/v1/object/public/${BUCKET}/${bookId}`;
	const playback_map = playbackMapRaw.map((entry) => ({
		...entry,
		audio_path: `${storageBase}/${entry.audio_path}`
	}));

	return { book, chapters, chunks, playback_map, checkpoints };
}
