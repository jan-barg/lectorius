<script lang="ts">
	import { playback } from '$lib/stores/playback';
	import type { PlaybackMapEntry, Chapter, Chunk } from '$lib/types';

	export let playbackMap: PlaybackMapEntry[];
	export let chapters: Chapter[];
	export let chunks: Chunk[];
	export let onSeek: (chunkIndex: number, offsetMs: number) => void;

	let chunkIndex = 1;
	let chunkTimeMs = 0;

	playback.subscribe((s) => {
		chunkIndex = s.chunk_index;
		chunkTimeMs = s.chunk_time_ms;
	});

	// Sort playback map by chunk_index for cumulative duration calculations
	$: sortedMap = [...playbackMap].sort((a, b) => a.chunk_index - b.chunk_index);
	$: totalDurationMs = sortedMap.reduce((sum, e) => sum + e.duration_ms, 0);

	$: elapsedMs = (() => {
		let elapsed = 0;
		for (const entry of sortedMap) {
			if (entry.chunk_index < chunkIndex) {
				elapsed += entry.duration_ms;
			} else if (entry.chunk_index === chunkIndex) {
				elapsed += chunkTimeMs;
				break;
			} else {
				break;
			}
		}
		return elapsed;
	})();

	$: progress = totalDurationMs > 0 ? (elapsedMs / totalDurationMs) * 100 : 0;

	// Hover tooltip state
	let barEl: HTMLDivElement;
	let showTooltip = false;
	let tooltipX = 0;
	let tooltipTime = '';
	let tooltipChapter = '';

	function positionToTarget(clientX: number): { chunkIndex: number; offsetMs: number; timeMs: number } {
		const rect = barEl.getBoundingClientRect();
		const pct = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
		const targetMs = pct * totalDurationMs;

		let cumulative = 0;
		for (const entry of sortedMap) {
			if (cumulative + entry.duration_ms > targetMs) {
				return {
					chunkIndex: entry.chunk_index,
					offsetMs: targetMs - cumulative,
					timeMs: targetMs
				};
			}
			cumulative += entry.duration_ms;
		}

		// Past the end — return last chunk at its end
		const last = sortedMap[sortedMap.length - 1];
		return { chunkIndex: last.chunk_index, offsetMs: last.duration_ms, timeMs: totalDurationMs };
	}

	function handleClick(e: MouseEvent) {
		const target = positionToTarget(e.clientX);
		onSeek(target.chunkIndex, target.offsetMs);
	}

	function handleMouseMove(e: MouseEvent) {
		const target = positionToTarget(e.clientX);
		const rect = barEl.getBoundingClientRect();
		tooltipX = e.clientX - rect.left;
		tooltipTime = formatTime(target.timeMs);

		// Find chapter for the target chunk
		const chunk = chunks.find((c) => c.chunk_index === target.chunkIndex);
		if (chunk) {
			const chapter = chapters.find((ch) => ch.chapter_id === chunk.chapter_id);
			tooltipChapter = chapter?.title ?? '';
		} else {
			tooltipChapter = '';
		}

		showTooltip = true;
	}

	function handleMouseLeave() {
		showTooltip = false;
	}

	function formatTime(ms: number): string {
		const totalSeconds = Math.floor(ms / 1000);
		const minutes = Math.floor(totalSeconds / 60);
		const seconds = totalSeconds % 60;
		return `${minutes}:${seconds.toString().padStart(2, '0')}`;
	}
</script>

<div class="w-full px-4">
	<!-- svelte-ignore a11y-click-events-have-key-events -->
	<!-- svelte-ignore a11y-no-static-element-interactions -->
	<div
		class="relative h-2 w-full cursor-pointer overflow-visible rounded-full bg-surface"
		bind:this={barEl}
		onclick={handleClick}
		onmousemove={handleMouseMove}
		onmouseleave={handleMouseLeave}
		role="slider"
		aria-valuemin={0}
		aria-valuemax={totalDurationMs}
		aria-valuenow={elapsedMs}
		aria-label="Seek through audiobook"
		tabindex="0"
	>
		<div
			class="absolute left-0 top-0 h-full rounded-full bg-accent transition-[width] duration-150"
			style="width: {progress}%"
		></div>

		{#if showTooltip}
			<div
				class="absolute bottom-full mb-2 -translate-x-1/2 whitespace-nowrap rounded bg-surface px-2 py-1 text-xs shadow-lg"
				style="left: {tooltipX}px"
			>
				<span class="text-text">{tooltipTime}</span>
				{#if tooltipChapter}
					<span class="ml-1 text-muted">{tooltipChapter}</span>
				{/if}
			</div>
		{/if}
	</div>

	<div class="mt-1 flex justify-between text-xs text-muted">
		<span>{formatTime(elapsedMs)}</span>
		<span>{formatTime(totalDurationMs)}</span>
	</div>
</div>
