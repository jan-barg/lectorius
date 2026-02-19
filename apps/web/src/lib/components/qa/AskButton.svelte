<script lang="ts">
	import { qa } from '$lib/stores/qa';
	import { playback } from '$lib/stores/playback';
	import { type Recorder, blobToBase64 } from '$lib/services/recorder';
	import { get } from 'svelte/store';
	import { onDestroy } from 'svelte';
	import { browser } from '$app/environment';

	export let bookId: string;
	export let onAnswerComplete: () => void;
	export let recorder: Recorder;

	let answerAudio: HTMLAudioElement | null = null;
	let audioQueue: string[] = [];
	let isPlayingAudio = false;
	let streamDone = false;
	let abortController: AbortController | null = null;
	let requestStartTime = 0;
	let firstAudioPlayed = false;

	let isRecording = false;
	let isProcessing = false;
	let isPlayingAnswer = false;

	const unsub = qa.subscribe((s) => {
		isRecording = s.is_recording;
		isProcessing = s.is_processing;
		isPlayingAnswer = s.is_playing_answer;
	});

	function playNextAudio() {
		if (audioQueue.length === 0) {
			isPlayingAudio = false;
			checkComplete();
			return;
		}

		isPlayingAudio = true;
		const audioBase64 = audioQueue.shift()!;
		answerAudio = new Audio(`data:audio/mp3;base64,${audioBase64}`);
		answerAudio.onplay = () => {
			if (!firstAudioPlayed) {
				console.log(`[qa] TIME TO FIRST AUDIO: ${Date.now() - requestStartTime}ms`);
				firstAudioPlayed = true;
			}
		};
		answerAudio.onended = playNextAudio;
		answerAudio.onerror = () => {
			console.error('[audio] Playback error');
			playNextAudio();
		};
		answerAudio.play().catch((e) => {
			console.error('[audio] Play failed:', e);
			playNextAudio();
		});
	}

	function checkComplete() {
		if (streamDone && !isPlayingAudio && audioQueue.length === 0) {
			setTimeout(() => {
				qa.reset();
				onAnswerComplete();
			}, 2000);
		}
	}

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

		requestStartTime = Date.now();
		firstAudioPlayed = false;
		const t0 = requestStartTime;
		console.log(`[qa] Button released`);

		try {
			const blob = await recorder.stopRecording();
			console.log(`[qa] Recording stopped: ${Date.now() - t0}ms, size: ${blob.size} bytes`);

			qa.stopRecording();

			const audio_base64 = await blobToBase64(blob);
			console.log(`[qa] Base64 converted: ${Date.now() - t0}ms`);

			const state = get(playback);

			abortController = new AbortController();
			const response = await fetch('/api/ask', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					book_id: bookId,
					chunk_index: state.chunk_index,
					chunk_time_ms: state.chunk_time_ms,
					audio_base64
				}),
				signal: abortController.signal
			});
			console.log(`[qa] Stream response received: ${Date.now() - t0}ms`);

			await handleStreamingResponse(response);
		} catch (e) {
			if (e instanceof DOMException && e.name === 'AbortError') return;
			console.error('Q&A failed:', e);
			qa.setError('Something went wrong');
			resumeAfterDelay();
		}
	}

	async function handleStreamingResponse(response: Response) {
		if (!response.body) {
			throw new Error('No response body');
		}

		const reader = response.body.getReader();
		const decoder = new TextDecoder();
		let sseBuffer = '';
		let questionText = '';
		let firstAudioReceived = false;

		audioQueue = [];
		isPlayingAudio = false;
		streamDone = false;

		try {
			while (true) {
				const { done, value } = await reader.read();
				if (done) break;

				sseBuffer += decoder.decode(value, { stream: true });
				const lines = sseBuffer.split('\n\n');
				sseBuffer = lines.pop() || '';

				for (const line of lines) {
					if (!line.startsWith('data: ')) continue;

					const data = JSON.parse(line.slice(6));

					if (data.type === 'question') {
						questionText = data.text;
						console.log(`[stream] Question: ${data.text}`);
					}

					if (data.type === 'audio') {
						console.log(`[stream] Audio chunk: "${data.text.substring(0, 30)}..."`);
						audioQueue.push(data.audio);

						if (!firstAudioReceived) {
							firstAudioReceived = true;
							qa.setAnswer(questionText, '');
						}

						if (!isPlayingAudio) {
							playNextAudio();
						}
					}

					if (data.type === 'done') {
						console.log(`[stream] Stream complete`);
						streamDone = true;
						checkComplete();
					}

					if (data.type === 'error') {
						console.error('[stream] Error:', data.error);
						if (data.fallback_audio_url) {
							playFallbackAudio(data.fallback_audio_url);
						} else {
							qa.setError(data.error || 'Something went wrong');
							resumeAfterDelay();
						}
						return;
					}
				}
			}

			// If stream ended without explicit 'done' event
			if (!streamDone) {
				streamDone = true;
				checkComplete();
			}
		} catch (e) {
			if (e instanceof DOMException && e.name === 'AbortError') return;
			console.error('[stream] Parse error:', e);
			qa.setError('Something went wrong');
			resumeAfterDelay();
		}
	}

	function playFallbackAudio(url: string) {
		qa.setError('Something went wrong');
		answerAudio = new Audio(url);
		answerAudio.onended = () => resumeAfterDelay();
		answerAudio.onerror = () => resumeAfterDelay();
		answerAudio.play().catch(() => resumeAfterDelay());
	}

	function resumeAfterDelay() {
		setTimeout(() => {
			qa.reset();
			onAnswerComplete();
		}, 2000);
	}

	function handleMouseEnter() {
		if (!browser || isProcessing || isPlayingAnswer) return;
		recorder.warmUp();
	}

	function handleTouchStart() {
		if (!browser || isProcessing || isPlayingAnswer) return;
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
		abortController?.abort();
		recorder.cancelRecording();
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
				: 'bg-accent text-white hover:bg-accent/80'}"
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
