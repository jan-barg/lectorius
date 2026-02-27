<script lang="ts">
	export let volume: number;
	export let onVolumeInput: (e: Event) => void;
	export let compact: boolean = false;
</script>

<div class="flex items-center {compact ? 'gap-1.5' : 'gap-2'}">
	<svg class="{compact ? 'h-3 w-3' : 'h-3.5 w-3.5'} shrink-0 text-muted/60" fill="currentColor" viewBox="0 0 24 24">
		<path d="M11 5L6 9H2v6h4l5 4V5zm2 3.17v7.66a6.5 6.5 0 000-7.66z" />
	</svg>
	<input
		type="range"
		min="0"
		max="100"
		value={volume}
		oninput={onVolumeInput}
		class="music-volume-slider h-3 cursor-pointer appearance-none rounded-full bg-transparent {compact ? 'w-16' : 'flex-1'}"
	/>
	{#if !compact}
		<span class="w-8 text-right text-[10px] font-medium tabular-nums text-muted/50">{volume}%</span>
	{/if}
</div>

<style>
	.music-volume-slider::-webkit-slider-thumb {
		-webkit-appearance: none;
		appearance: none;
		width: 10px;
		height: 10px;
		border-radius: 50%;
		background: rgb(var(--color-accent));
		cursor: pointer;
		margin-top: -3.5px; /* center 10px thumb on 3px track */
	}
	.music-volume-slider::-moz-range-thumb {
		width: 10px;
		height: 10px;
		border-radius: 50%;
		border: none;
		background: rgb(var(--color-accent));
		cursor: pointer;
	}
	.music-volume-slider::-webkit-slider-runnable-track {
		height: 3px;
		border-radius: 2px;
		background: rgb(var(--color-text) / 0.08);
	}
	.music-volume-slider::-moz-range-track {
		height: 3px;
		border-radius: 2px;
		background: rgb(var(--color-text) / 0.08);
	}
</style>
