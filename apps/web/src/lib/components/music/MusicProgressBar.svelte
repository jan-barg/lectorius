<script lang="ts">
	import { formatTime } from '$lib/utils/format';

	export let elapsedMs: number;
	export let totalMs: number;
	export let onSeek: (timeSeconds: number) => void;

	$: progress = totalMs > 0 ? Math.min((elapsedMs / totalMs) * 100, 100) : 0;

	function handleClick(e: MouseEvent) {
		const bar = e.currentTarget as HTMLElement;
		const rect = bar.getBoundingClientRect();
		const pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
		onSeek((pct * totalMs) / 1000);
	}
</script>

<div class="w-full group">
	<div
		class="relative h-[3px] w-full cursor-pointer overflow-visible rounded-full bg-text/[0.08] dark:bg-white/[0.08] py-2 bg-clip-content"
		onclick={handleClick}
		onkeydown={() => {}}
		role="slider"
		aria-valuemin={0}
		aria-valuemax={totalMs}
		aria-valuenow={elapsedMs}
		aria-label="Seek through song"
		tabindex="0"
	>
		<div
			class="absolute left-0 top-1/2 -translate-y-1/2 h-[3px] rounded-full bg-accent transition-[width] duration-150"
			style="width: {progress}%"
		>
			<div class="absolute right-0 top-1/2 -translate-y-1/2 translate-x-1/2 w-2.5 h-2.5 bg-accent rounded-full shadow-sm scale-0 opacity-0 transition-all duration-200 group-hover:scale-100 group-hover:opacity-100 pointer-events-none"></div>
		</div>
	</div>
	<div class="mt-1.5 flex justify-between text-[9px] font-medium tracking-wider tabular-nums text-muted/60 pointer-events-none">
		<span>{formatTime(elapsedMs)}</span>
		<span>{formatTime(totalMs)}</span>
	</div>
</div>
