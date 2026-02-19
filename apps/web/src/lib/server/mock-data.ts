import type { BookListItem, BookMeta, Chapter, Chunk, PlaybackMapEntry, MemoryCheckpoint } from '$lib/types';

export const MOCK_BOOKS: BookListItem[] = [
	{
		book_id: 'great-gatsby',
		title: 'The Great Gatsby',
		author: 'F. Scott Fitzgerald',
		cover_url: null,
		cover_video_url: null,
		total_chapters: 9,
		total_chunks: 90,
		total_duration_ms: 32400000
	},
	{
		book_id: 'rip-van-winkle',
		title: 'Rip Van Winkle',
		author: 'Washington Irving',
		cover_url: null,
		cover_video_url: null,
		total_chapters: 3,
		total_chunks: 30,
		total_duration_ms: 2640000
	},
	{
		book_id: 'yellow-wallpaper',
		title: 'The Yellow Wallpaper',
		author: 'Charlotte Perkins Gilman',
		cover_url: null,
		cover_video_url: null,
		total_chapters: 1,
		total_chunks: 10,
		total_duration_ms: 1920000
	}
];

export function getMockBookDetail(bookId: string) {
	const listItem = MOCK_BOOKS.find((b) => b.book_id === bookId);
	if (!listItem) return null;

	const book: BookMeta = {
		book_id: listItem.book_id,
		title: listItem.title,
		author: listItem.author,
		language: 'en',
		year: null,
		book_type: 'fiction',
		source: 'gutenberg',
		source_id: null
	};

	const chapters: Chapter[] = Array.from({ length: listItem.total_chapters }, (_, i) => ({
		book_id: bookId,
		chapter_id: `${bookId}_ch${String(i + 1).padStart(3, '0')}`,
		index: i + 1,
		title: `Chapter ${i + 1}`,
		char_start: i * 5000,
		char_end: (i + 1) * 5000
	}));

	const chunksPerChapter = 10;
	const chunks: Chunk[] = [];
	let globalIndex = 1;
	for (const chapter of chapters) {
		for (let j = 0; j < chunksPerChapter; j++) {
			chunks.push({
				book_id: bookId,
				chapter_id: chapter.chapter_id,
				chunk_id: `${chapter.chapter_id}_${String(globalIndex).padStart(6, '0')}`,
				chunk_index: globalIndex,
				text: `This is sample text for chunk ${globalIndex} of ${listItem.title}. The story continues with vivid descriptions and compelling narrative that draws the reader deeper into the world the author has created.`,
				char_start: chapter.char_start + j * 500,
				char_end: chapter.char_start + (j + 1) * 500
			});
			globalIndex++;
		}
	}

	const playbackMap: PlaybackMapEntry[] = chunks.map((c) => ({
		chunk_id: c.chunk_id,
		chapter_id: c.chapter_id,
		chunk_index: c.chunk_index,
		audio_path: `audio/chunks/${c.chunk_id}.mp3`,
		duration_ms: 4000,
		start_ms: 0,
		end_ms: 4000
	}));

	const checkpoints: MemoryCheckpoint[] = [
		{
			book_id: bookId,
			checkpoint_index: 1,
			until_chunk_index: Math.floor(chunks.length / 2),
			until_chunk_id: chunks[Math.floor(chunks.length / 2) - 1].chunk_id,
			summary: `The story of ${listItem.title} has been unfolding with the introduction of key characters and settings.`,
			entities: {
				people: [],
				places: [],
				open_threads: []
			}
		}
	];

	return { book, chapters, chunks, playback_map: playbackMap, checkpoints, cover_video_url: null };
}
