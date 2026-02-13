<script lang="ts">
	import { playback } from '$lib/stores/playback';
	import type { PlaybackSpeed } from '$lib/stores/types';

	export let onSkip: (seconds: number) => void;

	let isPlaying = false;
	let speed: PlaybackSpeed = 1;

	playback.subscribe((s) => {
		isPlaying = s.is_playing;
		speed = s.playback_speed;
	});

	function togglePlay() {
		if (isPlaying) {
			playback.pause();
		} else {
			playback.play();
		}
	}

	function cycleSpeed() {
		const speeds: PlaybackSpeed[] = [1, 1.5, 2];
		const next = speeds[(speeds.indexOf(speed) + 1) % speeds.length];
		playback.setSpeed(next);
	}
</script>

<div class="flex items-center justify-center gap-6">
	<button
		onclick={() => onSkip(-15)}
		class="flex h-10 w-10 items-center justify-center rounded-full text-muted transition-colors hover:text-text"
		aria-label="Skip back 15 seconds"
	>
		<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="h-5 w-5">
			<path d="M12.5 8c-2.65 0-5.05 1.04-6.83 2.73L3.5 8.5v7h7l-2.78-2.78C9.08 11.35 10.7 10.5 12.5 10.5c2.9 0 5.33 1.97 6.05 4.64l1.93-.51C19.56 11.1 16.34 8 12.5 8z"/>
		</svg>
		<span class="ml-0.5 text-[10px]">15</span>
	</button>

	<button
		onclick={togglePlay}
		class="flex h-16 w-16 items-center justify-center rounded-full bg-primary text-white transition-all hover:bg-primary/80 hover:scale-105"
		aria-label={isPlaying ? 'Pause' : 'Play'}
	>
		{#if isPlaying}
			<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="h-7 w-7">
				<path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>
			</svg>
		{:else}
			<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="h-7 w-7 ml-1">
				<path d="M8 5v14l11-7z"/>
			</svg>
		{/if}
	</button>

	<button
		onclick={() => onSkip(15)}
		class="flex h-10 w-10 items-center justify-center rounded-full text-muted transition-colors hover:text-text"
		aria-label="Skip forward 15 seconds"
	>
		<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="h-5 w-5">
			<path d="M11.5 8c2.65 0 5.05 1.04 6.83 2.73L20.5 8.5v7h-7l2.78-2.78C14.92 11.35 13.3 10.5 11.5 10.5c-2.9 0-5.33 1.97-6.05 4.64l-1.93-.51C4.44 11.1 7.66 8 11.5 8z"/>
		</svg>
		<span class="ml-0.5 text-[10px]">15</span>
	</button>

	<button
		onclick={cycleSpeed}
		class="flex h-8 min-w-[3rem] items-center justify-center rounded-full bg-surface px-2 text-sm font-medium text-muted transition-colors hover:text-text"
		aria-label="Change playback speed"
	>
		{speed}x
	</button>
</div>
