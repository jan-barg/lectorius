<script lang="ts">
	import type { BookListItem } from "$lib/types";
	import BookCard from "./BookCard.svelte";

	export let books: BookListItem[];
	export let startedBookIds: Set<string>;

	$: newBooks = books.filter((b) => !startedBookIds.has(b.book_id));
</script>

{#if newBooks.length > 0}
	<section class="mt-12 mb-8">
		<div class="mb-4 flex items-baseline justify-between">
			<h2 class="text-2xl font-bold text-text">Read Something New</h2>
			<span class="hidden text-sm font-medium text-muted md:inline-block">
				Scroll to explore &rarr;
			</span>
		</div>

		<div
			class="flex flex-row overflow-x-auto snap-x snap-mandatory gap-6 pb-12 pt-4 px-4 -mx-4 hide-scrollbar"
		>
			{#each newBooks as book (book.book_id)}
				<div class="flex-shrink-0 snap-start">
					<BookCard {book} />
				</div>
			{/each}
		</div>
	</section>
{/if}
