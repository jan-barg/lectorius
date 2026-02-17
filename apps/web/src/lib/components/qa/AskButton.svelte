<script lang="ts">
	import { qa } from '$lib/stores/qa';
	import { playback } from '$lib/stores/playback';
	import { type Recorder, blobToBase64 } from '$lib/services/recorder';
	import { get } from 'svelte/store';
	import { onDestroy } from 'svelte';
	import type { LoadedBook } from '$lib/types';

	export let bookId: string;
	export let onAnswerComplete: () => void;
	export let recorder: Recorder;
	export let loadedBook: LoadedBook;
	let answerAudio: HTMLAudioElement | null = null;

	let isRecording = false;
	let isProcessing = false;
	let isPlayingAnswer = false;

	const unsub = qa.subscribe((s) => {
		isRecording = s.is_recording;
		isProcessing = s.is_processing;
		isPlayingAnswer = s.is_playing_answer;
	});

	async function handlePointerDown() {
		if (isRecording || isProcessing || isPlayingAnswer) return;

		const t0 = Date.now();
		console.log(`[qa] Button pressed`);

		try {
			playback.pause();
			console.log(`[qa] Playback paused: ${Date.now() - t0}ms`);

			await recorder.startRecording();
			console.log(`[qa] Recording started: ${Date.now() - t0}ms`);

			qa.startRecording();
		} catch (e) {
			console.error('Failed to start recording:', e);
			qa.setError('Microphone access denied');
		}
	}

	async function handlePointerUp() {
		if (!isRecording) return;

		const t0 = Date.now();
		console.log(`[qa] Button released`);

		try {
			const blob = await recorder.stopRecording();
			console.log(`[qa] Recording stopped: ${Date.now() - t0}ms, size: ${blob.size} bytes`);

			qa.stopRecording();

			const audio_base64 = await blobToBase64(blob);
			console.log(`[qa] Base64 converted: ${Date.now() - t0}ms`);

			const state = get(playback);

			const response = await fetch('/api/ask', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					book_id: bookId,
					chunk_index: state.chunk_index,
					chunk_time_ms: state.chunk_time_ms,
					audio_base64,
					book: loadedBook.book,
					chapters: loadedBook.chapters,
					chunks: loadedBook.chunks,
					playback_map: loadedBook.playbackMap,
					checkpoints: loadedBook.checkpoints
				})
			});
			console.log(`[qa] API response received: ${Date.now() - t0}ms`);

			const data = await response.json();
			console.log(`[qa] JSON parsed: ${Date.now() - t0}ms`);

			if (data.success) {
				qa.setAnswer(data.question_text, data.answer_text);
				playResponseAudio(`data:audio/mp3;base64,${data.answer_audio}`);
				console.log(`[qa] Audio playback started: ${Date.now() - t0}ms`);
			} else {
				qa.setError(data.error || 'Something went wrong');
				if (data.fallback_audio_url) {
					playResponseAudio(data.fallback_audio_url);
				} else {
					resumeAfterDelay();
				}
			}
		} catch (e) {
			console.error('Q&A failed:', e);
			qa.setError('Something went wrong');
			resumeAfterDelay();
		}
	}

	function playResponseAudio(src: string) {
		answerAudio = new Audio(src);
		answerAudio.onended = () => resumeAfterDelay();
		answerAudio.onerror = () => resumeAfterDelay();
		answerAudio.play();
	}

	function resumeAfterDelay() {
		setTimeout(() => {
			qa.reset();
			onAnswerComplete();
		}, 2000);
	}

	function handleMouseEnter() {
		if (isProcessing || isPlayingAnswer) return;
		recorder.warmUp();
	}

	function handleTouchStart() {
		if (isProcessing || isPlayingAnswer) return;
		recorder.warmUp();
	}

	function handlePointerLeave() {
		if (isRecording) {
			recorder.cancelRecording();
			qa.reset();
			onAnswerComplete();
		} else {
			recorder.releaseWarmStream();
		}
	}

	onDestroy(() => {
		unsub();
		recorder.cancelRecording();
		// Don't releaseStream here — Player owns the stream lifecycle
		answerAudio?.pause();
		answerAudio = null;
	});
</script>

<button
	onmouseenter={handleMouseEnter}
	ontouchstart={handleTouchStart}
	onpointerdown={handlePointerDown}
	onpointerup={handlePointerUp}
	onpointerleave={handlePointerLeave}
	disabled={isProcessing || isPlayingAnswer}
	class="flex items-center gap-2 rounded-full px-6 py-3 text-sm font-medium transition-all
		{isRecording
		? 'bg-red-500 text-white animate-pulse'
		: isProcessing
			? 'bg-surface text-muted cursor-wait'
			: isPlayingAnswer
				? 'bg-green-600 text-white'
				: 'bg-secondary text-white hover:bg-secondary/80'}"
	aria-label={isRecording ? 'Release to send' : 'Hold to ask a question'}
>
	{#if isRecording}
		<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="h-5 w-5">
			<path
				d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"
			/>
			<path
				d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"
			/>
		</svg>
		Listening...
	{:else if isProcessing}
		<svg
			class="h-5 w-5 animate-spin"
			xmlns="http://www.w3.org/2000/svg"
			fill="none"
			viewBox="0 0 24 24"
		>
			<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"
			></circle>
			<path
				class="opacity-75"
				fill="currentColor"
				d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
			></path>
		</svg>
		Thinking...
	{:else if isPlayingAnswer}
		<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="h-5 w-5">
			<path
				d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z"
			/>
		</svg>
		Speaking...
	{:else}
		<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="h-5 w-5">
			<path
				d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"
			/>
			<path
				d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"
			/>
		</svg>
		Hold to Ask
	{/if}
</button>
