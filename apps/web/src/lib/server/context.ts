import type { Chunk, PlaybackMapEntry, MemoryCheckpoint } from '$lib/types';

/**
 * Get recent chunks around the playhead (~60 seconds of audio).
 */
export function getRecentChunks(
	chunks: Chunk[],
	playbackMap: PlaybackMapEntry[],
	currentChunkIndex: number,
	targetDurationMs: number = 60000
): Chunk[] {
	const result: Chunk[] = [];
	let totalDuration = 0;

	for (let i = currentChunkIndex; i >= 1 && totalDuration < targetDurationMs; i--) {
		const entry = playbackMap.find((p) => p.chunk_index === i);
		const chunk = chunks.find((c) => c.chunk_index === i);
		if (entry && chunk) {
			result.unshift(chunk);
			totalDuration += entry.duration_ms;
		}
	}
	return result;
}

/**
 * Get the latest memory checkpoint at or before the current chunk.
 */
export function getCurrentCheckpoint(
	checkpoints: MemoryCheckpoint[],
	currentChunkIndex: number
): MemoryCheckpoint | null {
	for (let i = checkpoints.length - 1; i >= 0; i--) {
		if (checkpoints[i].until_chunk_index <= currentChunkIndex) {
			return checkpoints[i];
		}
	}
	return null;
}
