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
	const chunkByIndex = new Map(chunks.map((c) => [c.chunk_index, c]));
	const durationByIndex = new Map(playbackMap.map((p) => [p.chunk_index, p.duration_ms]));

	const result: Chunk[] = [];
	let totalDuration = 0;

	for (let i = currentChunkIndex; i >= 1 && totalDuration < targetDurationMs; i--) {
		const duration = durationByIndex.get(i);
		const chunk = chunkByIndex.get(i);
		if (duration !== undefined && chunk) {
			result.unshift(chunk);
			totalDuration += duration;
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
