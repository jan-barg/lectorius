<script lang="ts">
	import type { Chapter } from '$lib/types';

	export let chapters: Chapter[];
	export let currentChapterId: string | null = null;
</script>

<div class="space-y-1">
	<h3 class="mb-3 text-sm font-semibold uppercase tracking-wider text-muted">Chapters</h3>
	{#each chapters as chapter (chapter.chapter_id)}
		<button
			class="w-full rounded-lg px-3 py-2 text-left text-sm transition-colors
				{chapter.chapter_id === currentChapterId
					? 'bg-primary/10 text-primary'
					: 'text-muted hover:bg-surface hover:text-text'}"
			aria-label="Jump to {chapter.title}"
		>
			<span class="mr-2 text-xs text-muted/60">{chapter.index}.</span>
			{chapter.title}
		</button>
	{/each}
</div>
