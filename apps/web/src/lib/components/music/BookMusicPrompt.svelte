<script lang="ts">
	import { music, playlists } from '$lib/stores/music';
	import { fly } from 'svelte/transition';
	import { browser } from '$app/environment';

	const SESSION_KEY = 'lectorius_music_prompts_shown';

	interface Props {
		bookTitle: string;
		bookPlaylistId: string;
		onDismiss: () => void;
	}

	let { bookTitle, bookPlaylistId, onDismiss }: Props = $props();

	let currentPlaylistName = $derived(
		$playlists.find((p) => p.playlist_id === $music.current_playlist_id)?.name ?? 'current music'
	);

	function markShown(): void {
		if (!browser) return;
		try {
			const shown: string[] = JSON.parse(sessionStorage.getItem(SESSION_KEY) || '[]');
			if (!shown.includes(bookPlaylistId)) {
				shown.push(bookPlaylistId);
				sessionStorage.setItem(SESSION_KEY, JSON.stringify(shown));
			}
		} catch {
			// sessionStorage unavailable
		}
	}

	function accept() {
		music.setPlaylist(bookPlaylistId);
		markShown();
		onDismiss();
	}

	function decline() {
		markShown();
		onDismiss();
	}
</script>

<div
	class="fixed bottom-24 left-5 right-5 sm:right-auto sm:w-96 z-40"
	transition:fly={{ y: 20, duration: 300 }}
>
	<div
		class="rounded-2xl border border-text/[0.05] dark:border-white/[0.05] bg-surface/95 shadow-2xl shadow-black/15 dark:shadow-black/40 backdrop-blur-2xl p-6 space-y-5"
	>
		<div class="flex items-start gap-3">
			<svg
				class="h-5 w-5 shrink-0 text-accent/60 mt-0.5"
				fill="none"
				stroke="currentColor"
				viewBox="0 0 24 24"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2z"
				/>
			</svg>
			<p class="text-sm text-text leading-relaxed">
				Would you like to listen to <span class="font-semibold text-accent">{bookTitle}</span> theme
				music?
			</p>
		</div>

		<div class="flex gap-2.5">
			<button
				class="flex-1 rounded-xl bg-text px-4 py-2.5 text-sm font-semibold text-background transition-all duration-300 hover:opacity-90 shadow-md shadow-text/10 dark:shadow-black/20"
				onclick={accept}
			>
				Yes
			</button>
			<button
				class="flex-1 rounded-xl border border-text/[0.05] dark:border-white/[0.05] bg-text/[0.02] dark:bg-white/[0.02] px-4 py-2.5 text-sm font-medium text-muted transition-all duration-300 hover:bg-text/[0.05] dark:hover:bg-white/[0.05] hover:text-text"
				onclick={decline}
			>
				No, keep {currentPlaylistName}
			</button>
		</div>
	</div>
</div>
