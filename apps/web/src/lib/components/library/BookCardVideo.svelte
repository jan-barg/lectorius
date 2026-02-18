<script lang="ts">
	export let src: string | null = null;
	export let hovering = false;
	export let fallbackChar = '?';

	let video: HTMLVideoElement;
	let failed = false;
	let ended = false;

	$: if (video && !failed) {
		if (hovering && !ended) {
			video.play().catch(() => {
				failed = true;
			});
		} else if (!hovering && !ended) {
			video.pause();
		}
	}
</script>

{#if src && !failed}
	<video
		bind:this={video}
		{src}
		muted
		playsinline
		preload="auto"
		class="h-full w-full object-cover"
		on:ended={() => (ended = true)}
		on:error={() => (failed = true)}
	></video>
{:else}
	<div class="flex h-full w-full items-center justify-center bg-background">
		<span class="text-5xl font-bold text-primary/30">{fallbackChar}</span>
	</div>
{/if}
