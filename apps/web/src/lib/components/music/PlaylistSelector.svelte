<script lang="ts">
	import type { Playlist } from '$lib/stores/music';

	export let playlists: Playlist[];
	export let currentPlaylistId: string | null;
	export let onSelectPlaylist: (playlistId: string) => void;

	let open = false;

	$: currentName = playlists.find((p) => p.playlist_id === currentPlaylistId)?.name ?? 'Select playlist';

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
		class="flex w-full items-center justify-between rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-text transition-colors hover:bg-white/10"
		onclick={() => (open = !open)}
	>
		<span class="truncate font-medium">{currentName}</span>
		<svg class="h-4 w-4 shrink-0 text-muted transition-transform {open ? 'rotate-180' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
		</svg>
	</button>

	{#if open}
		<div class="absolute bottom-full left-0 mb-1 w-full rounded-xl border border-white/10 bg-surface shadow-xl overflow-hidden z-10">
			{#each playlists as pl (pl.playlist_id)}
				<button
					class="flex w-full items-center px-4 py-2.5 text-sm transition-colors
						{pl.playlist_id === currentPlaylistId
							? 'bg-accent/15 text-text'
							: 'text-muted hover:bg-white/5 hover:text-text'}"
					onclick={() => select(pl)}
				>
					<span class="truncate">{pl.name}</span>
				</button>
			{/each}
		</div>
	{/if}
</div>
