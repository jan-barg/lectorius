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
	class="fixed bottom-20 left-4 right-4 sm:right-auto sm:w-96 z-40"
	transition:fly={{ y: 20, duration: 300 }}
>
	<div
		class="rounded-xl border border-text/[0.06] dark:border-white/[0.06] bg-surface/95 shadow-lg backdrop-blur-md p-5 space-y-4"
	>
		<div class="flex items-start gap-3">
			<svg
				class="h-5 w-5 shrink-0 text-accent/70 mt-0.5"
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
				class="flex-1 rounded-lg bg-text px-4 py-2.5 text-sm font-semibold text-background transition-all duration-200 hover:opacity-90"
				onclick={accept}
			>
				Yes
			</button>
			<button
				class="flex-1 rounded-lg border border-text/[0.06] dark:border-white/[0.06] bg-text/[0.03] dark:bg-white/[0.03] px-4 py-2.5 text-sm font-medium text-muted transition-all duration-200 hover:bg-text/[0.06] dark:hover:bg-white/[0.06] hover:text-text"
				onclick={decline}
			>
				No, keep {currentPlaylistName}
			</button>
		</div>
	</div>
</div>
