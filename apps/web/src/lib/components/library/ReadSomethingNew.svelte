<script lang="ts">
	import type { BookListItem } from "$lib/types";
	import BookCard from "./BookCard.svelte";

	export let books: BookListItem[];
	export let startedBookIds: Set<string>;

	$: newBooks = books.filter((b) => !startedBookIds.has(b.book_id));
</script>

{#if newBooks.length > 0}
	<section>
		<div class="mb-5 flex items-baseline justify-between">
			<h2 class="font-display text-2xl md:text-3xl font-light text-text tracking-tight">Read Something New</h2>
			<span class="hidden text-xs font-medium uppercase tracking-widest text-muted/60 md:inline-block">
				Scroll &rarr;
			</span>
		</div>

		<div
			class="flex flex-row overflow-x-auto snap-x snap-mandatory gap-5 md:gap-7 pb-8 pt-2 px-1 -mx-1 hide-scrollbar"
		>
			{#each newBooks as book (book.book_id)}
				<div class="flex-shrink-0 snap-start">
					<BookCard {book} />
				</div>
			{/each}
		</div>
	</section>
{/if}
