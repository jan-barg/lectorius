<script lang="ts">
	import { playback } from '$lib/stores/playback';
	import { book } from '$lib/stores/book';

	let chunkIndex = 1;
	let totalChunks = 1;

	playback.subscribe((s) => {
		chunkIndex = s.chunk_index;
	});

	book.subscribe((s) => {
		if (s.loaded_book) {
			totalChunks = s.loaded_book.chunks.length;
		}
	});

	$: progress = totalChunks > 0 ? ((chunkIndex - 1) / totalChunks) * 100 : 0;
</script>

<div class="w-full px-4">
	<div class="relative h-1.5 w-full overflow-hidden rounded-full bg-surface">
		<div
			class="absolute left-0 top-0 h-full rounded-full bg-primary transition-all"
			style="width: {progress}%"
		></div>
	</div>
	<div class="mt-1 flex justify-between text-xs text-muted">
		<span>Chunk {chunkIndex}</span>
		<span>{totalChunks} total</span>
	</div>
</div>
