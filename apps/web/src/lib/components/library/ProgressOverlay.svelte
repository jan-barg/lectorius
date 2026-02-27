<script lang="ts">
	export let percentage: number;
</script>

<div class="absolute right-0 bottom-0 left-0 h-[3px] bg-black/30">
	<div
		class="h-full bg-accent transition-all duration-700 ease-out"
		style="width: {Math.min(100, Math.max(0, percentage))}%"
	></div>
</div>
