// =============================================================================
// book metadata
// =============================================================================

export interface BookMeta {
	book_id: string;
	title: string;
	author: string | null;
	language: string;
	year: number | null;
	book_type: 'fiction' | 'non-fiction' | 'biography';
	source: string | null;
	source_id: string | null;
	status?: 'available' | 'coming_soon';
	tts_provider?: 'openai' | 'elevenlabs';
	voice_id?: string;
}

// =============================================================================
// manifest
// =============================================================================

export interface ManifestConfig {
	tts_voice_id: string;
	tts_model: string;
	chunk_target_chars: number;
	chunk_min_chars: number;
	chunk_max_chars: number;
	checkpoint_interval_chunks: number;
	embedding_model: string;
}

export interface ManifestStats {
	chapters: number;
	chunks: number;
	total_audio_duration_ms: number;
	total_chars: number;
}

export interface Manifest {
	book_id: string;
	version: number;
	created_at: string;
	updated_at: string;
	pipeline_version: string;
	stages_completed: string[];
	config: ManifestConfig;
	stats: ManifestStats;
}

// =============================================================================
// chapters
// =============================================================================

export interface Chapter {
	book_id: string;
	chapter_id: string;
	index: number;
	title: string;
	char_start: number;
	char_end: number;
}

// =============================================================================
// chunks
// =============================================================================

export interface Chunk {
	book_id: string;
	chapter_id: string;
	chunk_id: string;
	chunk_index: number;
	text: string;
	char_start: number;
	char_end: number;
}

// =============================================================================
// playback map
// =============================================================================

export interface PlaybackMapEntry {
	chunk_id: string;
	chapter_id: string;
	chunk_index: number;
	audio_path: string;
	duration_ms: number;
	start_ms: number;
	end_ms: number;
}

// =============================================================================
// memory checkpoints
// =============================================================================

export type PersonRole = 'protagonist' | 'antagonist' | 'supporting' | 'mentioned';
export type ThreadStatus = 'open' | 'resolved';

export interface Person {
	name: string;
	aliases: string[];
	role: PersonRole;
	description: string;
	first_chunk: number;
	last_chunk: number;
}

export interface Place {
	name: string;
	description: string;
	first_chunk: number;
	last_chunk: number;
}

export interface PlotThread {
	id: string;
	description: string;
	status: ThreadStatus;
	introduced_chunk: number;
	last_updated_chunk: number;
}

export interface Entities {
	people: Person[];
	places: Place[];
	open_threads: PlotThread[];
}

export interface MemoryCheckpoint {
	book_id: string;
	checkpoint_index: number;
	until_chunk_index: number;
	until_chunk_id: string;
	summary: string;
	entities: Entities;
}

// =============================================================================
// loaded book (client-side, in-memory)
// =============================================================================

export interface LoadedBook {
	book: BookMeta;
	chapters: Chapter[];
	chunks: Chunk[];
	playbackMap: PlaybackMapEntry[];
	checkpoints: MemoryCheckpoint[];
	cover_video_url: string | null;
}

// =============================================================================
// book library item
// =============================================================================

export interface BookListItem {
	book_id: string;
	title: string;
	author: string | null;
	cover_url: string | null;
	cover_video_url: string | null;
	total_chapters: number;
	total_chunks: number;
	total_duration_ms: number;
	status?: 'available' | 'coming_soon';
}

// =============================================================================
// api response types
// =============================================================================

export interface GetBookResponse {
	book: BookMeta;
	chapters: Chapter[];
	chunks: Chunk[];
	playback_map: PlaybackMapEntry[];
	checkpoints: MemoryCheckpoint[];
	cover_video_url: string | null;
}
