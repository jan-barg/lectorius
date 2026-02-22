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
		class="mb-3 px-2 text-[11px] font-bold uppercase tracking-widest text-muted/70"
	>
		Chapters
	</h3>

	<div
		class="flex-1 max-h-56 space-y-1.5 overflow-y-auto pr-2 [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-white/10 hover:[&::-webkit-scrollbar-thumb]:bg-white/20 transition-colors"
	>
		{#each chapters as chapter (chapter.chapter_id)}
			<button
				onclick={() => handleClick(chapter.chapter_id)}
				class="group flex w-full items-center rounded-xl px-4 py-3 text-left text-sm transition-all duration-200
                    {chapter.chapter_id === currentChapterId
					? 'bg-accent/15 border border-accent/20 text-text shadow-[0_4px_16px_rgba(var(--color-accent),0.1)] backdrop-blur-md'
					: 'border border-transparent text-muted hover:bg-surface/50 hover:text-text hover:border-white/5'}"
				aria-label="Jump to {chapter.title}"
			>
				<span
					class="mr-3 text-xs font-bold {chapter.chapter_id ===
					currentChapterId
						? 'text-accent'
						: 'text-muted/40 group-hover:text-muted/70 transition-colors'}"
				>
					{chapter.index}.
				</span>

				<span
					class="truncate font-medium {chapter.chapter_id ===
					currentChapterId
						? 'text-text'
						: ''}"
				>
					{chapter.title}
				</span>
			</button>
		{/each}
	</div>
</div>
