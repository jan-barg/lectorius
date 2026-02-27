<script lang="ts">
	import type { Song } from '$lib/stores/music';
	import { formatTime } from '$lib/utils/format';

	export let songs: Song[];
	export let currentSongIndex: number;
	export let onSelectSong: (index: number) => void;
</script>

<div class="max-h-40 space-y-0.5 overflow-y-auto pr-1 [&::-webkit-scrollbar]:w-1 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-text/5 dark:[&::-webkit-scrollbar-thumb]:bg-white/5 hover:[&::-webkit-scrollbar-thumb]:bg-text/10 dark:hover:[&::-webkit-scrollbar-thumb]:bg-white/10">
	{#each songs as song, i (song.file_url)}
		<button
			class="group flex w-full items-center rounded-xl px-3 py-2.5 text-left text-xs transition-all duration-300
				{i === currentSongIndex
					? 'bg-accent/[0.08] text-text'
					: 'text-muted hover:bg-text/[0.03] dark:hover:bg-white/[0.03] hover:text-text'}"
			onclick={() => onSelectSong(i)}
		>
			<span class="mr-3 w-4 text-right text-[10px] font-bold tabular-nums {i === currentSongIndex ? 'text-accent' : 'text-muted/25'}">
				{i + 1}
			</span>
			<span class="flex-1 truncate {i === currentSongIndex ? 'font-semibold' : ''}">{song.title}</span>
			<span class="ml-2 text-[10px] tabular-nums text-muted/40 font-medium">{formatTime(song.duration_ms)}</span>
		</button>
	{/each}
</div>
