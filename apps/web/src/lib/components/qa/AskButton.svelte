<script lang="ts">
	import { qa } from "$lib/stores/qa";
	import { playback } from "$lib/stores/playback";
	import { music } from "$lib/stores/music";
	import { type Recorder, blobToBase64 } from "$lib/services/recorder";
	import { get } from "svelte/store";
	import { onDestroy } from "svelte";
	import { browser } from "$app/environment";

	export let bookId: string;
	export let onAnswerComplete: () => void;
	export let recorder: Recorder;

	let answerAudio: HTMLAudioElement | null = null;
	let audioQueue: string[] = [];
	let isPlayingAudio = false;
	let streamDone = false;
	let abortController: AbortController | null = null;

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
		answerAudio.onended = playNextAudio;
		answerAudio.onerror = () => {
			console.error("[audio] Playback error");
			playNextAudio();
		};
		answerAudio.play().catch((e) => {
			console.error("[audio] Play failed:", e);
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

		try {
			music.duck();
			playback.pause();
			await recorder.startRecording();
			qa.startRecording();
		} catch (e) {
			console.error("Failed to start recording:", e);
			qa.setError("Microphone access denied");
		}
	}

	async function handlePointerUp() {
		if (!isRecording) return;
		music.unduck();

		try {
			const blob = await recorder.stopRecording();
			qa.stopRecording();

			const audio_base64 = await blobToBase64(blob);

			const state = get(playback);

			abortController = new AbortController();
			const response = await fetch("/api/ask", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({
					book_id: bookId,
					chunk_index: state.chunk_index,
					chunk_time_ms: state.chunk_time_ms,
					audio_base64,
				}),
				signal: abortController.signal,
			});

			if (!response.ok) {
				console.error(`[qa] API error: ${response.status} ${response.statusText}`);
				let errorData: Record<string, string> | null = null;
				try {
					errorData = await response.json();
				} catch {}
				if (errorData?.fallback_audio_url) {
					playFallbackAudio(errorData.fallback_audio_url);
				} else {
					qa.setError(errorData?.error || "Something went wrong");
					resumeAfterDelay();
				}
				return;
			}

			await handleStreamingResponse(response);
		} catch (e) {
			if (e instanceof DOMException && e.name === "AbortError") return;
			console.error("Q&A failed:", e);
			qa.setError("Something went wrong");
			resumeAfterDelay();
		}
	}

	async function handleStreamingResponse(response: Response) {
		if (!response.body) {
			throw new Error("No response body");
		}

		const reader = response.body.getReader();
		const decoder = new TextDecoder();
		let sseBuffer = "";
		let questionText = "";
		let firstAudioReceived = false;

		audioQueue = [];
		isPlayingAudio = false;
		streamDone = false;

		try {
			while (true) {
				const { done, value } = await reader.read();
				if (done) break;

				sseBuffer += decoder.decode(value, { stream: true });
				const lines = sseBuffer.split("\n\n");
				sseBuffer = lines.pop() || "";

				for (const line of lines) {
					if (!line.startsWith("data: ")) continue;

					const data = JSON.parse(line.slice(6));

					if (data.type === "question") {
						questionText = data.text;
					}

					if (data.type === "audio") {
						audioQueue.push(data.audio);

						if (!firstAudioReceived) {
							firstAudioReceived = true;
							qa.setAnswer(questionText, "");
						}

						if (!isPlayingAudio) {
							playNextAudio();
						}
					}

					if (data.type === "done") {
						streamDone = true;
						checkComplete();
					}

					if (data.type === "error") {
						console.error("[stream] Error:", data.error);
						if (data.fallback_audio_url) {
							playFallbackAudio(data.fallback_audio_url);
						} else {
							qa.setError(data.error || "Something went wrong");
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
			if (e instanceof DOMException && e.name === "AbortError") return;
			console.error("[stream] Parse error:", e);
			qa.setError("Something went wrong");
			resumeAfterDelay();
		}
	}

	function playFallbackAudio(url: string) {
		qa.setError("Something went wrong");
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
			music.unduck();
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
		music.unduck();
		answerAudio?.pause();
		answerAudio = null;
	});
</script>

<div
	class="relative inline-flex items-center justify-center group touch-none select-none isolate"
>
	<button
		onmouseenter={handleMouseEnter}
		ontouchstart={handleTouchStart}
		onpointerdown={handlePointerDown}
		onpointerup={handlePointerUp}
		onpointerleave={handlePointerLeave}
		oncontextmenu={(e) => e.preventDefault()}
		disabled={isProcessing || isPlayingAnswer}
		class="relative z-10 flex items-center justify-center gap-3 px-8 py-4 w-48 rounded-full font-bold text-lg tracking-wide overflow-hidden transition-all duration-500 bg-surface text-text border border-white/5
            {!isRecording && !isProcessing && !isPlayingAnswer
			? 'hover:bg-surface/80 hover:shadow-[0_0_30px_rgba(var(--color-accent),0.3)] active:scale-95'
			: ''}
            {isProcessing
			? 'shadow-[0_0_40px_rgba(var(--color-accent),0.6)] border-accent/50'
			: ''}"
		aria-label={isRecording ? "Release to send" : "Hold to ask a question"}
	>
		<div
			class="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[150%] aspect-square rounded-full transition-transform duration-700 ease-in-out pointer-events-none -z-10
                {isRecording
				? 'bg-accent scale-100'
				: isPlayingAnswer
					? 'bg-accent/90 scale-100'
					: 'scale-0 bg-transparent'}"
		></div>

		<div
			class="relative z-20 flex items-center justify-center gap-3 w-full transition-colors duration-500
            {isRecording || isPlayingAnswer ? 'text-white' : ''}
            {isProcessing ? 'text-accent' : ''}"
		>
			<div
				class="relative w-6 h-6 flex-shrink-0 flex items-center justify-center"
			>
				<svg
					class="absolute inset-0 w-full h-full transition-all duration-300 {isProcessing ||
					isPlayingAnswer
						? 'scale-50 opacity-0'
						: 'scale-100 opacity-100'}"
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
					stroke-width="2"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
					/>
				</svg>

				<div
					class="absolute inset-0 w-full h-full transition-all duration-300 {isProcessing
						? 'scale-100 opacity-100'
						: 'scale-50 opacity-0'}"
				>
					<svg
						class="w-full h-full animate-spin"
						xmlns="http://www.w3.org/2000/svg"
						fill="none"
						viewBox="0 0 24 24"
					>
						<circle
							class="opacity-25"
							cx="12"
							cy="12"
							r="10"
							stroke="currentColor"
							stroke-width="3"
						></circle>
						<path
							class="opacity-75"
							fill="currentColor"
							d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
						></path>
					</svg>
				</div>

				<div
					class="absolute inset-0 flex items-center justify-center gap-[3px] transition-all duration-300 {isPlayingAnswer
						? 'scale-100 opacity-100'
						: 'scale-50 opacity-0'}"
				>
					<div class="wave wave-1"></div>
					<div class="wave wave-2"></div>
					<div class="wave wave-3"></div>
					<div class="wave wave-4"></div>
				</div>
			</div>

			<span class="whitespace-nowrap w-24 text-left">
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
	/* Bulletproof CSS Wave Animation */
	.wave {
		width: 3px;
		height: 6px; /* Default height */
		background-color: white;
		border-radius: 9999px;
		animation: wave-anim ease-in-out infinite;
	}

	/* Unique timings for organic bounce */
	.wave-1 {
		animation-duration: 0.7s;
		animation-delay: -0.2s;
	}
	.wave-2 {
		animation-duration: 1s;
		animation-delay: -0.4s;
	}
	.wave-3 {
		animation-duration: 0.6s;
		animation-delay: -0.1s;
	}
	.wave-4 {
		animation-duration: 0.8s;
		animation-delay: -0.3s;
	}

	@keyframes wave-anim {
		0%,
		100% {
			height: 6px;
		}
		50% {
			height: 22px;
		}
	}
</style>
