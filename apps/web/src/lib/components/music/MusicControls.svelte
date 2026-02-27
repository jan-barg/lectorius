<script lang="ts">
	export let isPlaying: boolean;
	export let isLooping: boolean;
	export let onPlay: () => void;
	export let onPause: () => void;
	export let onSkip: () => void;
	export let onRewind: () => void;
	export let onToggleLoop: () => void;
</script>

<div class="flex items-center justify-center gap-3">
	<!-- Rewind -->
	<button
		class="flex h-9 w-9 items-center justify-center rounded-full text-muted transition-all duration-200 hover:text-text active:scale-90"
		onclick={onRewind}
		aria-label="Previous song"
	>
		<svg class="h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
			<path d="M6 6h2v12H6zm3.5 6l8.5 6V6z" />
		</svg>
	</button>

	<!-- Play/Pause -->
	<button
		class="flex h-10 w-10 items-center justify-center rounded-full bg-text text-background transition-all duration-200 hover:scale-105 active:scale-95"
		onclick={() => (isPlaying ? onPause() : onPlay())}
		aria-label={isPlaying ? 'Pause' : 'Play'}
	>
		{#if isPlaying}
			<svg class="h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
				<path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z" />
			</svg>
		{:else}
			<svg class="h-4 w-4 ml-0.5" fill="currentColor" viewBox="0 0 24 24">
				<path d="M8 5v14l11-7z" />
			</svg>
		{/if}
	</button>

	<!-- Skip -->
	<button
		class="flex h-9 w-9 items-center justify-center rounded-full text-muted transition-all duration-200 hover:text-text active:scale-90"
		onclick={onSkip}
		aria-label="Next song"
	>
		<svg class="h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
			<path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z" />
		</svg>
	</button>

	<!-- Loop -->
	<button
		class="flex h-9 w-9 items-center justify-center rounded-full transition-all duration-200 active:scale-90
			{isLooping
				? 'text-accent bg-accent/10'
				: 'text-muted hover:text-text'}"
		onclick={onToggleLoop}
		aria-label="Toggle loop"
	>
		<svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
			<path stroke-linecap="round" stroke-linejoin="round" d="M17 1l4 4-4 4" />
			<path stroke-linecap="round" stroke-linejoin="round" d="M3 11V9a4 4 0 014-4h14" />
			<path stroke-linecap="round" stroke-linejoin="round" d="M7 23l-4-4 4-4" />
			<path stroke-linecap="round" stroke-linejoin="round" d="M21 13v2a4 4 0 01-4 4H3" />
		</svg>
	</button>
</div>
