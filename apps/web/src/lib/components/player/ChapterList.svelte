<script lang="ts">
	import type { Chapter, Chunk } from '$lib/types';

	export let chapters: Chapter[];
	export let chunks: Chunk[];
	export let currentChapterId: string | null = null;
	export let onChapterSelect: (chunkIndex: number) => void;

	function handleClick(chapterId: string) {
		const firstChunk = chunks.find((c) => c.chapter_id === chapterId);
		if (firstChunk) {
			onChapterSelect(firstChunk.chunk_index);
		}
	}
</script>

<div class="space-y-1">
	<h3 class="mb-3 text-sm font-semibold uppercase tracking-wider text-muted">Chapters</h3>
	{#each chapters as chapter (chapter.chapter_id)}
		<button
			onclick={() => handleClick(chapter.chapter_id)}
			class="w-full rounded-lg px-3 py-2 text-left text-sm transition-colors
				{chapter.chapter_id === currentChapterId
					? 'bg-accent/10 text-accent'
					: 'text-muted hover:bg-surface hover:text-text'}"
			aria-label="Jump to {chapter.title}"
		>
			<span class="mr-2 text-xs text-muted/60">{chapter.index}.</span>
			{chapter.title}
		</button>
	{/each}
</div>
