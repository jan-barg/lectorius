<script lang="ts">
	import Greeting from '$lib/components/library/Greeting.svelte';
	import WelcomeCard from '$lib/components/library/WelcomeCard.svelte';
	import TextureBar from '$lib/components/ui/TextureBar.svelte';
	import ContinueReading from '$lib/components/library/ContinueReading.svelte';
	import ReadSomethingNew from '$lib/components/library/ReadSomethingNew.svelte';
	import type { BookListItem } from '$lib/types';
	import { getReadingHistory, type ReadingHistoryEntry } from '$lib/stores/reading-history';
	import { onMount, onDestroy } from 'svelte';
	import { browser } from '$app/environment';

	let books: BookListItem[] = [];
	let history: ReadingHistoryEntry[] = [];
	let loading = true;
	let error: string | null = null;
	let showWelcome = browser ? !localStorage.getItem('lectorius_user') : false;

	function refreshHistory() {
		history = getReadingHistory();
	}

	onMount(async () => {
		refreshHistory();
		window.addEventListener('readinghistorychange', refreshHistory);
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

	onDestroy(() => {
		if (typeof window !== 'undefined') {
			window.removeEventListener('readinghistorychange', refreshHistory);
		}
	});

	$: startedBookIds = new Set(history.map((h) => h.book_id));
</script>

<svelte:head>
	<title>lectorius</title>
</svelte:head>

<div class="mx-auto max-w-5xl px-4 py-12">
	<Greeting />
	<TextureBar />

	{#if loading}
		<div class="flex justify-center py-20">
			<div class="h-8 w-8 animate-spin rounded-full border-2 border-accent border-t-transparent"></div>
		</div>
	{:else if error}
		<p class="text-center text-red-400">{error}</p>
	{:else}
		<div class="space-y-10">
			<ContinueReading {books} {history} />
			<ReadSomethingNew {books} {startedBookIds} />
		</div>
	{/if}
</div>

{#if showWelcome}
	<WelcomeCard onComplete={() => (showWelcome = false)} />
{/if}
