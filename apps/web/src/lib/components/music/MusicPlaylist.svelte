<script lang="ts">
	import type { Song } from '$lib/stores/music';
	import { formatTime } from '$lib/utils/format';

	export let songs: Song[];
	export let currentSongIndex: number;
	export let onSelectSong: (index: number) => void;
</script>

<div class="max-h-44 space-y-1 overflow-y-auto pr-1 [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-white/10 hover:[&::-webkit-scrollbar-thumb]:bg-white/20">
	{#each songs as song, i (song.file_url)}
		<button
			class="group flex w-full items-center rounded-xl px-3 py-2.5 text-left text-sm transition-all duration-200
				{i === currentSongIndex
					? 'bg-accent/15 border border-accent/20 text-text'
					: 'border border-transparent text-muted hover:bg-surface/50 hover:text-text hover:border-white/5'}"
			onclick={() => onSelectSong(i)}
		>
			<span class="mr-3 w-5 text-right text-xs font-bold {i === currentSongIndex ? 'text-accent' : 'text-muted/40'}">
				{i + 1}.
			</span>
			<span class="flex-1 truncate font-medium">{song.title}</span>
			<span class="ml-2 text-xs text-muted/60">{formatTime(song.duration_ms)}</span>
		</button>
	{/each}
</div>
