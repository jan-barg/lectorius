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
		class="mb-4 px-1 text-[10px] font-bold uppercase tracking-[0.2em] text-muted/40"
	>
		Chapters
	</h3>

	<div
		class="flex-1 max-h-60 space-y-0.5 overflow-y-auto pr-1 [&::-webkit-scrollbar]:w-1 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-text/5 dark:[&::-webkit-scrollbar-thumb]:bg-white/5 hover:[&::-webkit-scrollbar-thumb]:bg-text/10 dark:hover:[&::-webkit-scrollbar-thumb]:bg-white/10 transition-colors"
	>
		{#each chapters as chapter (chapter.chapter_id)}
			<button
				onclick={() => handleClick(chapter.chapter_id)}
				class="group flex w-full items-center rounded-xl px-3.5 py-3 text-left text-sm transition-all duration-300
                    {chapter.chapter_id === currentChapterId
					? 'bg-accent/[0.08] text-text'
					: 'text-muted hover:bg-text/[0.03] dark:hover:bg-white/[0.03] hover:text-text'}"
				aria-label="Jump to {chapter.title}"
			>
				<span
					class="mr-4 w-5 text-right text-[11px] font-bold tabular-nums {chapter.chapter_id ===
					currentChapterId
						? 'text-accent'
						: 'text-muted/25 group-hover:text-muted/40 transition-colors duration-300'}"
				>
					{chapter.index}
				</span>

				<span
					class="truncate font-display text-[15px] {chapter.chapter_id ===
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
