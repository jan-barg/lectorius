<script lang="ts">
	import type { Chapter, Chunk } from "$lib/types";

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

<div class="flex w-full flex-col">
	<h3
		class="mb-3 px-1 text-[10px] font-semibold uppercase tracking-[0.15em] text-muted/60"
	>
		Chapters
	</h3>

	<div
		class="flex-1 max-h-56 space-y-0.5 overflow-y-auto pr-1 [&::-webkit-scrollbar]:w-1 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-text/5 dark:[&::-webkit-scrollbar-thumb]:bg-white/5 hover:[&::-webkit-scrollbar-thumb]:bg-text/10 dark:hover:[&::-webkit-scrollbar-thumb]:bg-white/10 transition-colors"
	>
		{#each chapters as chapter (chapter.chapter_id)}
			<button
				onclick={() => handleClick(chapter.chapter_id)}
				class="group flex w-full items-center rounded-lg px-3 py-2.5 text-left text-sm transition-all duration-200
                    {chapter.chapter_id === currentChapterId
					? 'bg-accent/10 text-text'
					: 'text-muted hover:bg-text/[0.03] dark:hover:bg-white/[0.03] hover:text-text'}"
				aria-label="Jump to {chapter.title}"
			>
				<span
					class="mr-3 w-5 text-right text-[11px] font-semibold tabular-nums {chapter.chapter_id ===
					currentChapterId
						? 'text-accent'
						: 'text-muted/30 group-hover:text-muted/50 transition-colors'}"
				>
					{chapter.index}
				</span>

				<span
					class="truncate {chapter.chapter_id ===
					currentChapterId
						? 'font-medium text-text'
						: 'font-normal'}"
				>
					{chapter.title}
				</span>
			</button>
		{/each}
	</div>
</div>
