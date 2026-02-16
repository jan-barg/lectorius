<script lang="ts">
	import type { LoadedBook } from '$lib/types';
	import Controls from './Controls.svelte';
	import ProgressBar from './ProgressBar.svelte';
	import ChapterList from './ChapterList.svelte';
	import AskButton from '$lib/components/qa/AskButton.svelte';
	import { playback, savePosition, loadSavedPosition } from '$lib/stores/playback';
	import { AudioEngine } from '$lib/services/audio';
	import { Recorder } from '$lib/services/recorder';
	import { onMount, onDestroy } from 'svelte';
	import { get } from 'svelte/store';

	export let loadedBook: LoadedBook;

	const totalChunks = loadedBook.chunks.length;
	let engine: AudioEngine | null = null;
	let saveInterval: ReturnType<typeof setInterval> | null = null;
	let currentChapterId: string | null = null;
	const recorder = new Recorder();
	let streamAcquired = false;

	// Track previous store values to detect changes
	let prevChunkIndex = 0;
	let prevIsPlaying = false;
	let prevSpeed = 1;
	let restoredSeekMs: number | null = null;

	function handleChunkEnd() {
		const state = get(playback);
		if (state.chunk_index >= totalChunks) {
			playback.pause();
			savePosition();
			return;
		}
		playback.nextChunk(totalChunks);
		savePosition();
		const newState = get(playback);
		engine?.play(newState.chunk_index);
	}

	function handleTimeUpdate(ms: number) {
		playback.setChunkTime(ms);
	}

	function handleSkip(seconds: number) {
		if (!engine) return;
		const state = get(playback);
		const deltaMs = seconds * 1000;
		const currentMs = state.chunk_time_ms;
		const chunkDuration = engine.getDurationMs(state.chunk_index);

		if (deltaMs > 0) {
			// Skip forward
			if (currentMs + deltaMs < chunkDuration) {
				engine.seekTo(currentMs + deltaMs);
			} else if (state.chunk_index < totalChunks) {
				const remainder = deltaMs - (chunkDuration - currentMs);
				playback.nextChunk(totalChunks);
				savePosition();
				const newState = get(playback);
				engine.play(newState.chunk_index, remainder);
			}
		} else {
			// Skip back
			const absDelta = Math.abs(deltaMs);
			if (currentMs > absDelta) {
				engine.seekTo(currentMs - absDelta);
			} else if (state.chunk_index > 1) {
				const remainder = absDelta - currentMs;
				playback.prevChunk();
				savePosition();
				const newState = get(playback);
				const prevDuration = engine.getDurationMs(newState.chunk_index);
				const seekTarget = Math.max(0, prevDuration - remainder);
				engine.play(newState.chunk_index, seekTarget);
			} else {
				engine.seekTo(0);
			}
		}
	}

	function handleSeek(chunkIndex: number, offsetMs: number) {
		playback.setChunk(chunkIndex);
		playback.setChunkTime(offsetMs);
		savePosition();
		engine?.play(chunkIndex, offsetMs);
	}

	function handleChapterSelect(chunkIndex: number) {
		playback.setChunk(chunkIndex);
		playback.play();
		savePosition();
		engine?.play(chunkIndex);
	}

	function startSaveInterval() {
		stopSaveInterval();
		saveInterval = setInterval(savePosition, 5000);
	}

	function stopSaveInterval() {
		if (saveInterval) {
			clearInterval(saveInterval);
			saveInterval = null;
		}
	}

	function handleBeforeUnload() {
		savePosition();
	}

	onMount(() => {
		// Restore saved position
		const saved = loadSavedPosition(loadedBook.book.book_id);
		if (saved) {
			playback.setChunk(saved.chunk_index);
			playback.setChunkTime(saved.chunk_time_ms);
			restoredSeekMs = saved.chunk_time_ms;
		}

		engine = new AudioEngine(loadedBook.playbackMap, {
			onChunkEnd: handleChunkEnd,
			onTimeUpdate: handleTimeUpdate
		});

		window.addEventListener('beforeunload', handleBeforeUnload);
	});

	const unsub = playback.subscribe((state) => {
		// Update current chapter
		const chunk = loadedBook.chunks.find((c) => c.chunk_index === state.chunk_index);
		currentChapterId = chunk?.chapter_id ?? null;

		if (!engine) return;

		// React to chunk_index changes
		if (state.chunk_index !== prevChunkIndex) {
			if (state.is_playing) {
				const seekMs = restoredSeekMs ?? undefined;
				restoredSeekMs = null;
				engine.play(state.chunk_index, seekMs);
			}
			prevChunkIndex = state.chunk_index;
		}

		// React to play/pause changes
		if (state.is_playing !== prevIsPlaying) {
			if (state.is_playing) {
				// Acquire mic stream on first play (user gesture satisfies browser requirement)
				if (!streamAcquired) {
					streamAcquired = true;
					recorder.acquireStream().catch((e) => {
						console.warn('[player] Mic stream acquire failed (non-blocking):', e);
					});
				}

				if (engine.getCurrentTimeMs() === 0 && prevChunkIndex === state.chunk_index) {
					const seekMs = restoredSeekMs ?? undefined;
					restoredSeekMs = null;
					engine.play(state.chunk_index, seekMs);
				} else {
					engine.resume();
				}
				startSaveInterval();
			} else {
				engine.pause();
				stopSaveInterval();
				savePosition();
			}
			prevIsPlaying = state.is_playing;
		}

		// React to speed changes
		if (state.playback_speed !== prevSpeed) {
			engine.setSpeed(state.playback_speed);
			prevSpeed = state.playback_speed;
		}
	});

	onDestroy(() => {
		unsub();
		stopSaveInterval();
		savePosition();
		engine?.destroy();
		engine = null;
		recorder.releaseStream();
		window.removeEventListener('beforeunload', handleBeforeUnload);
	});
</script>

<div class="mx-auto flex max-w-2xl flex-col gap-8">
	<!-- Book info -->
	<div class="text-center">
		<h1 class="text-2xl font-bold text-text">{loadedBook.book.title}</h1>
		{#if loadedBook.book.author}
			<p class="mt-1 text-muted">{loadedBook.book.author}</p>
		{/if}
	</div>

	<!-- Cover placeholder -->
	<div class="mx-auto flex h-64 w-64 items-center justify-center rounded-2xl bg-surface">
		<span class="text-6xl font-bold text-primary/20">
			{loadedBook.book.title.charAt(0)}
		</span>
	</div>

	<!-- Progress -->
	<ProgressBar
		playbackMap={loadedBook.playbackMap}
		chapters={loadedBook.chapters}
		chunks={loadedBook.chunks}
		onSeek={handleSeek}
	/>

	<!-- Controls -->
	<Controls onSkip={handleSkip} />

	<!-- Ask button -->
	<div class="flex justify-center">
		<AskButton
			bookId={loadedBook.book.book_id}
			{recorder}
			onAnswerComplete={() => playback.play()}
		/>
	</div>

	<!-- Chapter list -->
	<div class="rounded-xl bg-surface/50 p-4">
		<ChapterList
			chapters={loadedBook.chapters}
			{currentChapterId}
			chunks={loadedBook.chunks}
			onChapterSelect={handleChapterSelect}
		/>
	</div>
</div>
