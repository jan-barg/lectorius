<script lang="ts">
	export let percentage: number;
</script>

<div class="absolute right-0 bottom-0 left-0 h-1 bg-black/30">
	<div
		class="h-full bg-primary transition-all duration-300"
		style="width: {Math.min(100, Math.max(0, percentage))}%"
	></div>
</div>
