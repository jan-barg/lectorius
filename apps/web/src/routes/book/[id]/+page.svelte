<script lang="ts">
	import { page } from '$app/stores';
	import { onMount, onDestroy, tick } from 'svelte';
	import { browser } from '$app/environment';
	import Player from '$lib/components/player/Player.svelte';
	import BookMusicPrompt from '$lib/components/music/BookMusicPrompt.svelte';
	import { book } from '$lib/stores/book';
	import { playback } from '$lib/stores/playback';
	import { playlists, currentBookId, music } from '$lib/stores/music';
	import { get } from 'svelte/store';
	import type { BookStoreState } from '$lib/stores/types';
	import type { GetBookResponse } from '$lib/types';

	const SESSION_KEY = 'lectorius_music_prompts_shown';

	let bookId = '';

	const unsubPage = page.subscribe((p) => {
		bookId = p.params.id ?? '';
	});

	let showMusicPrompt = false;
	let bookPlaylistId = '';
	let promptTimer: ReturnType<typeof setTimeout> | null = null;

	onMount(async () => {
		currentBookId.set(bookId);
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

		// Deferred music prompt check — runs after page has fully rendered
		await tick();
		promptTimer = setTimeout(() => {
			if (!browser) return;
			const cached = get(playlists);
			if (cached.length === 0) return;

			const match = cached.find((p) => p.type === 'book' && p.book_id === bookId);
			if (!match) return;

			// Already playing this book's playlist
			if (get(music).current_playlist_id === match.playlist_id) return;

			try {
				const shown: string[] = JSON.parse(sessionStorage.getItem(SESSION_KEY) || '[]');
				if (shown.includes(bookId)) return;
			} catch {
				return;
			}

			bookPlaylistId = match.playlist_id;
			showMusicPrompt = true;
		}, 500);
	});

	onDestroy(() => {
		unsubPage();
		book.clear();
		playback.reset();
		currentBookId.set(null);
		if (promptTimer) clearTimeout(promptTimer);
	});

	let bookState: BookStoreState;
	const unsubBook = book.subscribe((s) => { bookState = s; });
	onDestroy(() => unsubBook());
</script>

<svelte:head>
	<title>{bookState?.loaded_book?.book.title ?? 'Loading...'} | Lectorius</title>
</svelte:head>

<div class="mx-auto max-w-5xl py-6">
	<a href="/" class="mb-6 inline-flex items-center gap-1.5 text-xs font-medium uppercase tracking-widest text-muted transition-colors duration-200 hover:text-text">
		<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="h-3.5 w-3.5">
			<path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
		</svg>
		Library
	</a>

	{#if bookState?.is_loading}
		<div class="flex justify-center py-24">
			<div class="h-6 w-6 animate-spin rounded-full border-[1.5px] border-accent border-t-transparent"></div>
		</div>
	{:else if bookState?.error}
		<p class="text-center text-sm text-red-400/80 font-medium">{bookState.error}</p>
	{:else if bookState?.loaded_book}
		<Player loadedBook={bookState.loaded_book} />
	{/if}
</div>

{#if showMusicPrompt && bookState?.loaded_book}
	<BookMusicPrompt
		bookTitle={bookState.loaded_book.book.title}
		{bookPlaylistId}
		onDismiss={() => (showMusicPrompt = false)}
	/>
{/if}
