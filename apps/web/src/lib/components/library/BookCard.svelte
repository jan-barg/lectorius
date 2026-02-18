<script lang="ts">
	import type { BookListItem } from '$lib/types';
	import BookCardVideo from './BookCardVideo.svelte';
	import ProgressOverlay from './ProgressOverlay.svelte';

	export let book: BookListItem;
	export let progress: number | null = null;

	let hovering = false;

	function formatDuration(ms: number): string {
		const hours = Math.floor(ms / 3600000);
		const minutes = Math.floor((ms % 3600000) / 60000);
		if (hours > 0) return `${hours}h ${minutes}m`;
		return `${minutes}m`;
	}
</script>

<a
	href="/book/{book.book_id}"
	class="group block overflow-hidden rounded-xl bg-surface transition-all duration-200 hover:-translate-y-1 hover:ring-2 hover:ring-primary/50"
	on:mouseenter={() => (hovering = true)}
	on:mouseleave={() => (hovering = false)}
>
	<!-- Cover area -->
	<div class="relative aspect-[3/4] overflow-hidden">
		<BookCardVideo
			src={book.cover_video_url}
			{hovering}
			fallbackChar={book.title.charAt(0)}
		/>

		<!-- Gradient overlay with metadata -->
		<div class="pointer-events-none absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/70 to-transparent p-4 pt-12">
			<h3 class="text-sm font-semibold text-white">{book.title}</h3>
			{#if book.author}
				<p class="mt-0.5 text-xs text-white/70">{book.author}</p>
			{/if}
		</div>

		<!-- Progress bar -->
		{#if progress !== null}
			<ProgressOverlay percentage={progress} />
		{/if}
	</div>

	<!-- Info below cover -->
	<div class="px-3 py-2">
		<div class="flex items-center gap-2 text-xs text-muted">
			<span>{book.total_chapters} chapters</span>
			<span class="text-muted/50">|</span>
			<span>{formatDuration(book.total_duration_ms)}</span>
		</div>
	</div>
</a>
