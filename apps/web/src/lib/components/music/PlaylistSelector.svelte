<script lang="ts">
	import type { Playlist } from '$lib/stores/music';
	import { currentBookId } from '$lib/stores/music';

	export let playlists: Playlist[];
	export let currentPlaylistId: string | null;
	export let onSelectPlaylist: (playlistId: string) => void;

	let open = false;

	$: currentName = playlists.find((p) => p.playlist_id === currentPlaylistId)?.name ?? 'Select playlist';
	$: selectablePlaylists = playlists.filter((p) =>
		p.type === 'general' || (p.type === 'book' && p.book_id === $currentBookId)
	);

	function select(pl: Playlist) {
		onSelectPlaylist(pl.playlist_id);
		open = false;
	}
</script>

{#if open}
	<button
		class="fixed inset-0 z-[5]"
		onclick={() => (open = false)}
		aria-label="Close dropdown"
	></button>
{/if}

<div class="relative">
	<button
		class="flex w-full items-center justify-between rounded-lg border border-text/[0.06] dark:border-white/[0.06] bg-text/[0.02] dark:bg-white/[0.02] px-3.5 py-2.5 text-sm text-text transition-colors hover:bg-text/[0.04] dark:hover:bg-white/[0.04]"
		onclick={() => (open = !open)}
	>
		<span class="truncate font-medium">{currentName}</span>
		<svg class="h-4 w-4 shrink-0 text-muted/50 transition-transform duration-200 {open ? 'rotate-180' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
		</svg>
	</button>

	{#if open}
		<div class="absolute bottom-full left-0 mb-1 w-full rounded-lg border border-text/[0.06] dark:border-white/[0.06] bg-surface shadow-lg overflow-hidden z-10">
			{#each selectablePlaylists as pl (pl.playlist_id)}
				<button
					class="flex w-full items-center gap-2 px-3.5 py-2.5 text-sm transition-colors duration-150
						{pl.playlist_id === currentPlaylistId
							? 'bg-accent/10 text-text'
							: 'text-muted hover:bg-text/[0.03] dark:hover:bg-white/[0.03] hover:text-text'}"
					onclick={() => select(pl)}
				>
					{#if pl.type === 'book'}
						<svg class="h-3.5 w-3.5 shrink-0 text-accent/60" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
						</svg>
					{/if}
					<span class="truncate">{pl.name}</span>
				</button>
			{/each}
		</div>
	{/if}
</div>
