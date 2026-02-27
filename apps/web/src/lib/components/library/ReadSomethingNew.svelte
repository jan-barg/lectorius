<script lang="ts">
	import type { BookListItem } from "$lib/types";
	import BookCard from "./BookCard.svelte";

	export let books: BookListItem[];
	export let startedBookIds: Set<string>;

	$: newBooks = books.filter((b) => !startedBookIds.has(b.book_id));
</script>

{#if newBooks.length > 0}
	<section class="animate-fade-in-up stagger-3">
		<div class="mb-7 flex items-baseline justify-between">
			<h2 class="font-display text-3xl md:text-4xl font-light text-text tracking-tight">Read Something New</h2>
			<span class="hidden text-[10px] font-semibold uppercase tracking-[0.2em] text-muted/40 md:inline-block">
				Scroll &rarr;
			</span>
		</div>

		<div
			class="flex flex-row overflow-x-auto snap-x snap-mandatory gap-6 md:gap-8 pb-4 pt-2 px-1 -mx-1 hide-scrollbar"
		>
			{#each newBooks as book (book.book_id)}
				<div class="flex-shrink-0 snap-start">
					<BookCard {book} />
				</div>
			{/each}
		</div>
	</section>
{/if}
