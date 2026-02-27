<script lang="ts">
	import { onDestroy } from 'svelte';

	export let src: string | null = null;
	export let hovering = false;
	export let fallbackChar = '?';

	let video: HTMLVideoElement;
	let failed = false;
	let ended = false;
	let inView = false;
	let container: HTMLDivElement;
	let observer: IntersectionObserver | null = null;

	function setupObserver(node: HTMLDivElement) {
		observer = new IntersectionObserver(
			([entry]) => {
				if (entry.isIntersecting) {
					inView = true;
					observer?.disconnect();
					observer = null;
				}
			},
			{ rootMargin: '0px 200px 0px 0px' }
		);
		observer.observe(node);
	}

	$: if (container && src && !inView) {
		setupObserver(container);
	}

	$: videoSrc = inView && src && !failed ? src : null;

	$: if (video && !failed) {
		if (hovering && !ended) {
			video.play().catch(() => {
				failed = true;
			});
		} else if (!hovering && !ended) {
			video.pause();
		}
	}

	onDestroy(() => {
		observer?.disconnect();
	});
</script>

<div bind:this={container} class="h-full w-full">
	{#if videoSrc}
		<video
			bind:this={video}
			src={videoSrc}
			muted
			playsinline
			preload="auto"
			class="h-full w-full object-cover"
			onended={() => (ended = true)}
			onerror={() => (failed = true)}
		></video>
	{:else}
		<div class="flex h-full w-full items-center justify-center bg-surface dark:bg-surface">
			<span class="font-display text-6xl italic text-accent/20">{fallbackChar}</span>
		</div>
	{/if}
</div>
