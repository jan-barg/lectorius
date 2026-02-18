<script lang="ts">
	import type { BookListItem } from '$lib/types';
	import type { ReadingHistoryEntry } from '$lib/stores/reading-history';
	import BookCard from './BookCard.svelte';

	export let books: BookListItem[];
	export let history: ReadingHistoryEntry[];

	$: historyMap = new Map(history.map((h) => [h.book_id, h]));

	$: sortedBooks = books
		.filter((b) => historyMap.has(b.book_id))
		.sort((a, b) => {
			const aTime = historyMap.get(a.book_id)?.last_played ?? 0;
			const bTime = historyMap.get(b.book_id)?.last_played ?? 0;
			return bTime - aTime;
		});
</script>

{#if sortedBooks.length > 0}
	<section>
		<h2 class="mb-4 text-lg font-semibold text-muted">Continue Reading</h2>
		<div class="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
			{#each sortedBooks as book (book.book_id)}
				{@const entry = historyMap.get(book.book_id)}
				<BookCard
					{book}
					progress={entry ? (entry.last_chunk_index / entry.total_chunks) * 100 : null}
				/>
			{/each}
		</div>
	</section>
{/if}
