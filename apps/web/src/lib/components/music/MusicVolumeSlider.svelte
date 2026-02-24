<script lang="ts">
	export let volume: number;
	export let onVolumeInput: (e: Event) => void;
	export let compact: boolean = false;
</script>

<div class="flex items-center {compact ? 'gap-1.5' : 'gap-2'}">
	<svg class="{compact ? 'h-3.5 w-3.5' : 'h-4 w-4'} shrink-0 text-muted" fill="currentColor" viewBox="0 0 24 24">
		<path d="M11 5L6 9H2v6h4l5 4V5zm2 3.17v7.66a6.5 6.5 0 000-7.66z" />
	</svg>
	<input
		type="range"
		min="0"
		max="100"
		value={volume}
		oninput={onVolumeInput}
		class="music-volume-slider h-1 cursor-pointer appearance-none rounded-full bg-white/10 {compact ? 'w-16' : 'flex-1'}"
	/>
	{#if !compact}
		<span class="w-8 text-right text-[10px] font-medium text-muted">{volume}%</span>
	{/if}
</div>

<style>
	.music-volume-slider::-webkit-slider-thumb {
		-webkit-appearance: none;
		appearance: none;
		width: 12px;
		height: 12px;
		border-radius: 50%;
		background: rgb(var(--color-accent));
		cursor: pointer;
	}
	.music-volume-slider::-moz-range-thumb {
		width: 12px;
		height: 12px;
		border-radius: 50%;
		border: none;
		background: rgb(var(--color-accent));
		cursor: pointer;
	}
	.music-volume-slider::-webkit-slider-runnable-track {
		height: 4px;
		border-radius: 2px;
	}
	.music-volume-slider::-moz-range-track {
		height: 4px;
		border-radius: 2px;
		background: rgba(255, 255, 255, 0.1);
	}
</style>
