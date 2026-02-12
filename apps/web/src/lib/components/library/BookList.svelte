<script lang="ts">
	import type { BookListItem } from '$lib/types';
	import BookCard from './BookCard.svelte';

	export let books: BookListItem[];
</script>

<div class="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
	{#each books as book (book.book_id)}
		<BookCard {book} />
	{/each}
</div>
