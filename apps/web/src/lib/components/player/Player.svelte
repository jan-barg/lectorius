<script lang="ts">
	import type { LoadedBook } from '$lib/types';
	import Controls from './Controls.svelte';
	import ProgressBar from './ProgressBar.svelte';
	import ChapterList from './ChapterList.svelte';
	import AskButton from '$lib/components/qa/AskButton.svelte';
	import { playback } from '$lib/stores/playback';

	export let loadedBook: LoadedBook;

	let currentChapterId: string | null = null;

	playback.subscribe((s) => {
		const chunk = loadedBook.chunks.find((c) => c.chunk_index === s.chunk_index);
		currentChapterId = chunk?.chapter_id ?? null;
	});
</script>

<div class="mx-auto flex max-w-2xl flex-col gap-8">
	<!-- Book info -->
	<div class="text-center">
		<h1 class="text-2xl font-bold text-text">{loadedBook.book.title}</h1>
		{#if loadedBook.book.author}
			<p class="mt-1 text-muted">{loadedBook.book.author}</p>
		{/if}
	</div>

	<!-- Cover placeholder -->
	<div class="mx-auto flex h-64 w-64 items-center justify-center rounded-2xl bg-surface">
		<span class="text-6xl font-bold text-primary/20">
			{loadedBook.book.title.charAt(0)}
		</span>
	</div>

	<!-- Progress -->
	<ProgressBar />

	<!-- Controls -->
	<Controls />

	<!-- Ask button -->
	<div class="flex justify-center">
		<AskButton />
	</div>

	<!-- Chapter list -->
	<div class="rounded-xl bg-surface/50 p-4">
		<ChapterList chapters={loadedBook.chapters} {currentChapterId} />
	</div>
</div>
