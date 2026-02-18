<script lang="ts">
	import type { BookListItem } from '$lib/types';
	import BookCard from './BookCard.svelte';

	export let books: BookListItem[];
	export let startedBookIds: Set<string>;

	$: newBooks = books.filter((b) => !startedBookIds.has(b.book_id));
</script>

{#if newBooks.length > 0}
	<section>
		<h2 class="mb-4 text-lg font-semibold text-muted">Read Something New</h2>
		<div class="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
			{#each newBooks as book (book.book_id)}
				<BookCard {book} />
			{/each}
		</div>
	</section>
{/if}
