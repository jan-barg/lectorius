<script lang="ts">
	import { page } from '$app/stores';
	import { onMount, onDestroy } from 'svelte';
	import Player from '$lib/components/player/Player.svelte';
	import { book } from '$lib/stores/book';
	import { playback } from '$lib/stores/playback';
	import type { BookStoreState } from '$lib/stores/types';
	import type { GetBookResponse } from '$lib/types';

	let bookId = '';

	const unsubPage = page.subscribe((p) => {
		bookId = p.params.id ?? '';
	});

	onMount(async () => {
		book.startLoading();

		try {
			const res = await fetch(`/api/books/${bookId}`);
			if (!res.ok) throw new Error('Book not found');

			const data: GetBookResponse = await res.json();

			book.setBook({
				book: data.book,
				chapters: data.chapters,
				chunks: data.chunks,
				playbackMap: data.playback_map,
				checkpoints: data.checkpoints,
				cover_video_url: data.cover_video_url
			});

			playback.setBook(bookId);
		} catch (e) {
			book.setError(e instanceof Error ? e.message : 'Failed to load book');
		}
	});

	onDestroy(() => {
		unsubPage();
		book.clear();
		playback.reset();
	});

	let bookState: BookStoreState;
	const unsubBook = book.subscribe((s) => { bookState = s; });
	onDestroy(() => unsubBook());
</script>

<svelte:head>
	<title>{bookState?.loaded_book?.book.title ?? 'Loading...'} | lectorius</title>
</svelte:head>

<div class="mx-auto max-w-5xl px-4 py-8">
	<a href="/" class="mb-8 inline-flex items-center gap-1 text-sm text-muted transition-colors hover:text-text">
		<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="h-4 w-4">
			<path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
		</svg>
		Library
	</a>

	{#if bookState?.is_loading}
		<div class="flex justify-center py-20">
			<div class="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent"></div>
		</div>
	{:else if bookState?.error}
		<p class="text-center text-red-400">{bookState.error}</p>
	{:else if bookState?.loaded_book}
		<Player loadedBook={bookState.loaded_book} />
	{/if}
</div>
