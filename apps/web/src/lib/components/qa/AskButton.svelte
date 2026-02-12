<script lang="ts">
	import { qa } from '$lib/stores/qa';

	let isRecording = false;
	let isProcessing = false;

	qa.subscribe((s) => {
		isRecording = s.is_recording;
		isProcessing = s.is_processing;
	});

	function handlePress() {
		if (isRecording) {
			qa.stopRecording();
		} else {
			qa.startRecording();
		}
	}
</script>

<button
	onclick={handlePress}
	disabled={isProcessing}
	class="flex items-center gap-2 rounded-full px-6 py-3 text-sm font-medium transition-all
		{isRecording
			? 'bg-red-500 text-white animate-pulse'
			: isProcessing
				? 'bg-surface text-muted cursor-wait'
				: 'bg-secondary text-white hover:bg-secondary/80'}"
	aria-label={isRecording ? 'Stop recording' : 'Ask a question'}
>
	{#if isRecording}
		<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="h-5 w-5">
			<path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
			<path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
		</svg>
		Listening...
	{:else if isProcessing}
		<svg class="h-5 w-5 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
			<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
			<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
		</svg>
		Thinking...
	{:else}
		<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="h-5 w-5">
			<path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
			<path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
		</svg>
		Ask a question
	{/if}
</button>
