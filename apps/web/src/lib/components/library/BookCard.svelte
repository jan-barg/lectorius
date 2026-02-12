<script lang="ts">
	import type { BookListItem } from '$lib/types';

	export let book: BookListItem;

	function formatDuration(ms: number): string {
		const hours = Math.floor(ms / 3600000);
		const minutes = Math.floor((ms % 3600000) / 60000);
		if (hours > 0) return `${hours}h ${minutes}m`;
		return `${minutes}m`;
	}
</script>

<a
	href="/book/{book.book_id}"
	class="block rounded-xl bg-surface p-6 transition-all hover:ring-2 hover:ring-primary/50 hover:scale-[1.02]"
>
	<div class="mb-4 flex h-48 items-center justify-center rounded-lg bg-background">
		{#if book.cover_url}
			<img src={book.cover_url} alt={book.title} class="h-full w-auto rounded-lg object-cover" />
		{:else}
			<div class="text-center">
				<div class="text-4xl font-bold text-primary/30">
					{book.title.charAt(0)}
				</div>
			</div>
		{/if}
	</div>

	<h3 class="text-lg font-semibold text-text">{book.title}</h3>

	{#if book.author}
		<p class="mt-1 text-sm text-muted">{book.author}</p>
	{/if}

	<div class="mt-3 flex items-center gap-3 text-xs text-muted">
		<span>{book.total_chapters} chapters</span>
		<span class="text-muted/50">|</span>
		<span>{formatDuration(book.total_duration_ms)}</span>
	</div>
</a>
