<script lang="ts">
	import type { BookListItem } from "$lib/types";
	import type { ReadingHistoryEntry } from "$lib/stores/reading-history";
	import BookCard from "./BookCard.svelte";

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
		<div class="mb-5 flex items-baseline justify-between">
			<h2 class="font-display text-2xl md:text-3xl font-light text-text tracking-tight">Continue Reading</h2>
		</div>

		<div
			class="flex flex-row overflow-x-auto snap-x snap-mandatory gap-5 md:gap-7 pb-8 pt-2 px-1 -mx-1 hide-scrollbar"
		>
			{#each sortedBooks as book (book.book_id)}
				{@const entry = historyMap.get(book.book_id)}
				<div class="flex-shrink-0 snap-start">
					<BookCard
						{book}
						progress={entry
							? (entry.last_chunk_index / entry.total_chunks) *
								100
							: null}
					/>
				</div>
			{/each}
		</div>
	</section>
{/if}
