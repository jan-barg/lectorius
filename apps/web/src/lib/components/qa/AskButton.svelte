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

<div class="relative inline-flex items-center justify-center group touch-none select-none isolate">
	<!-- Warm hover glow (idle only) -->
	<div
		class="absolute inset-0 rounded-full bg-orange-400/30 blur-xl transition-all duration-700 ease-out -z-10
			{!isRecording && !isProcessing && !isPlayingAnswer
				? 'opacity-0 group-hover:opacity-100 group-hover:scale-125'
				: 'opacity-0'}"
	></div>

	<!-- Spinning conic border (thinking only) -->
	{#if isProcessing}
		<div
			class="absolute -inset-[3px] rounded-full -z-10 animate-spin-border"
			style="background: conic-gradient(from var(--angle), transparent, rgb(var(--color-accent)), transparent);"
		></div>
	{/if}

	<button
		onmouseenter={handleMouseEnter}
		ontouchstart={handleTouchStart}
		onpointerdown={handlePointerDown}
		onpointerup={handlePointerUp}
		onpointerleave={handlePointerLeave}
		oncontextmenu={(e) => e.preventDefault()}
		disabled={isProcessing || isPlayingAnswer}
		class="relative z-10 flex items-center justify-center gap-3 px-8 py-4 rounded-full font-bold text-lg tracking-wide overflow-hidden transition-all duration-300 bg-stone-100 dark:bg-slate-800 text-stone-900 dark:text-slate-50 active:scale-95"
		aria-label={isRecording ? 'Release to send' : 'Hold to ask a question'}
	>
		<!-- Color fill circle (expands for recording/speaking) -->
		<div
			class="absolute inset-0 m-auto w-[200%] h-[200%] rounded-full transition-transform duration-500 ease-out origin-center pointer-events-none -z-10
				{isRecording
					? 'bg-accent scale-100'
					: isPlayingAnswer
						? 'bg-emerald-500 dark:bg-emerald-400 scale-100'
						: 'scale-0 bg-transparent'}"
		></div>

		<div class="relative z-20 flex items-center gap-3 transition-colors duration-300
			{isRecording || isPlayingAnswer ? 'text-white' : ''}">

			{#if !isPlayingAnswer}
				<svg
					class="w-6 h-6 transition-all duration-300 {isProcessing ? 'scale-0 opacity-0 w-0' : 'scale-100 opacity-100'}"
					fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
				>
					<path stroke-linecap="round" stroke-linejoin="round" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
				</svg>
			{/if}

			{#if isPlayingAnswer}
				<svg
					class="w-6 h-6 animate-gentle-bounce"
					fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
				>
					<path stroke-linecap="round" stroke-linejoin="round" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
				</svg>
			{/if}

			<span class="whitespace-nowrap">
				{#if isRecording}
					Listening...
				{:else if isProcessing}
					Thinking...
				{:else if isPlayingAnswer}
					Speaking...
				{:else}
					Hold to Ask
				{/if}
			</span>
		</div>
	</button>
</div>

<style>
	@keyframes gentle-bounce {
		0%, 100% { transform: translateY(0); }
		50% { transform: translateY(-2px); }
	}
	.animate-gentle-bounce {
		animation: gentle-bounce 2s ease-in-out infinite;
	}
</style>
