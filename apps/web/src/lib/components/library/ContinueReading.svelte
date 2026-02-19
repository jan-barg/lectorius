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
	<section class="mb-8">
		<div class="mb-4 flex items-baseline justify-between">
			<h2 class="text-2xl font-bold text-text">Continue Reading</h2>
		</div>

		<div class="-mx-2 -mt-4 flex flex-nowrap gap-6 overflow-x-auto px-2 pt-4 pb-8 snap-x snap-mandatory scroll-smooth">
			{#each sortedBooks as book (book.book_id)}
				{@const entry = historyMap.get(book.book_id)}
				<div class="w-44 flex-shrink-0 snap-start sm:w-52">
					<BookCard
						{book}
						progress={entry ? (entry.last_chunk_index / entry.total_chunks) * 100 : null}
					/>
				</div>
			{/each}
			<div class="w-2 flex-shrink-0"></div>
		</div>
	</section>
{/if}

<style>
	.overflow-x-auto::-webkit-scrollbar {
		display: none;
	}
	.overflow-x-auto {
		-ms-overflow-style: none;
		scrollbar-width: none;
	}
</style>
