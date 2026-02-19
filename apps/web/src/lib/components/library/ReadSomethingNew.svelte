<script lang="ts">
	import type { BookListItem } from '$lib/types';
	import BookCard from './BookCard.svelte';

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

		<div class="-mx-2 -mt-4 flex flex-nowrap gap-6 overflow-x-auto px-2 pt-4 pb-8 snap-x snap-mandatory scroll-smooth">
			{#each newBooks as book (book.book_id)}
				<div class="w-36 flex-shrink-0 snap-start sm:w-40">
					<BookCard {book} />
				</div>
			{/each}
			<!-- End spacer -->
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
