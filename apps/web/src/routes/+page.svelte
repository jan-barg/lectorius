<script lang="ts">
	import BookList from '$lib/components/library/BookList.svelte';
	import type { BookListItem } from '$lib/types';
	import { onMount } from 'svelte';

	let books: BookListItem[] = [];
	let loading = true;
	let error: string | null = null;

	onMount(async () => {
		try {
			const res = await fetch('/api/books');
			const data = await res.json();
			books = data.books;
		} catch (e) {
			error = 'Failed to load books';
		} finally {
			loading = false;
		}
	});
</script>

<svelte:head>
	<title>lectorius</title>
</svelte:head>

<div class="mx-auto max-w-5xl px-4 py-12">
	<header class="mb-12 text-center">
		<h1 class="text-4xl font-bold text-text">lectorius</h1>
		<p class="mt-2 text-muted">interactive audiobooks that answer your questions</p>
	</header>

	{#if loading}
		<div class="flex justify-center py-20">
			<div class="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent"></div>
		</div>
	{:else if error}
		<p class="text-center text-red-400">{error}</p>
	{:else}
		<BookList {books} />
	{/if}
</div>
