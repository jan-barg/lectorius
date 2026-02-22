<script lang="ts">
	import type { LoadedBook } from "$lib/types";
	import Controls from "./Controls.svelte";
	import ProgressBar from "./ProgressBar.svelte";
	import ChapterList from "./ChapterList.svelte";
	import AskButton from "$lib/components/qa/AskButton.svelte";
	import {
		playback,
		savePosition,
		loadSavedPosition,
	} from "$lib/stores/playback";
	import { updateReadingHistory } from "$lib/stores/reading-history";
	import { AudioEngine } from "$lib/services/audio";
	import { Recorder } from "$lib/services/recorder";
	import { onMount, onDestroy } from "svelte";
	import { get } from "svelte/store";

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
	let prevVolume = 1;
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
		playback.play();
		savePosition();
		engine?.play(chunkIndex, offsetMs);
	}

	function handleChapterSelect(chunkIndex: number) {
		playback.setChunk(chunkIndex);
		playback.play();
		savePosition();
		engine?.play(chunkIndex);
	}

	function saveAll() {
		savePosition();
		const state = get(playback);
		if (state.book_id) {
			updateReadingHistory(state.book_id, state.chunk_index, totalChunks);
		}
	}

	function startSaveInterval() {
		stopSaveInterval();
		saveInterval = setInterval(saveAll, 5000);
	}

	function stopSaveInterval() {
		if (saveInterval) {
			clearInterval(saveInterval);
			saveInterval = null;
		}
	}

	function handleBeforeUnload() {
		saveAll();
	}

	onMount(() => {
		// Restore saved position
		const saved = loadSavedPosition(loadedBook.book.book_id);
		if (saved) {
			playback.setChunk(saved.chunk_index);
			playback.setChunkTime(saved.chunk_time_ms);
			restoredSeekMs = saved.chunk_time_ms;
		}

		// Record that this book has been opened
		updateReadingHistory(
			loadedBook.book.book_id,
			saved?.chunk_index ?? 1,
			totalChunks,
		);

		engine = new AudioEngine(loadedBook.playbackMap, {
			onChunkEnd: handleChunkEnd,
			onTimeUpdate: handleTimeUpdate,
		});

		window.addEventListener("beforeunload", handleBeforeUnload);
	});

	const unsub = playback.subscribe((state) => {
		// Update current chapter
		const chunk = loadedBook.chunks.find(
			(c) => c.chunk_index === state.chunk_index,
		);
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
					recorder.acquireStream().catch(() => {});
				}

				if (
					engine.getCurrentTimeMs() === 0 &&
					prevChunkIndex === state.chunk_index
				) {
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

		// React to volume changes
		if (state.volume !== prevVolume) {
			engine.setVolume(state.volume);
			prevVolume = state.volume;
		}
	});

	onDestroy(() => {
		unsub();
		stopSaveInterval();
		saveAll();
		engine?.destroy();
		engine = null;
		recorder.releaseStream();
		window.removeEventListener("beforeunload", handleBeforeUnload);
	});
</script>

<div
	class="relative w-full h-[calc(100vh-5rem)] overflow-y-auto overflow-x-hidden pt-6 pb-12 flex flex-col items-center"
>
	<div
		class="absolute left-1/2 top-40 -translate-x-1/2 w-[500px] h-[500px] bg-accent/15 rounded-full blur-[100px] pointer-events-none z-[-1]"
	></div>

	<div
		class="w-full max-w-xl mx-auto px-4 flex flex-col items-center text-center z-10"
	>
		<div class="mb-6">
			<h1
				class="font-outfit text-2xl md:text-3xl font-extrabold text-text drop-shadow-sm tracking-tight mb-1"
			>
				{loadedBook.book.title}
			</h1>
			{#if loadedBook.book.author}
				<p
					class="font-serif text-base md:text-lg italic text-muted drop-shadow-sm"
				>
					{loadedBook.book.author}
				</p>
			{/if}
		</div>

		<div
			class="relative w-48 md:w-56 aspect-[3/4] rounded-xl overflow-hidden shadow-[0_20px_40px_-10px_rgba(0,0,0,0.5)] ring-1 ring-white/10 mb-8 bg-surface transition-transform duration-500 hover:scale-[1.02]"
		>
			{#if loadedBook.cover_video_url}
				<video
					src={loadedBook.cover_video_url}
					preload="auto"
					muted
					class="absolute inset-0 h-full w-full object-cover"
					on:loadeddata={(e) => (e.currentTarget.currentTime = 0)}
				></video>
			{:else}
				<div
					class="absolute inset-0 flex h-full w-full items-center justify-center bg-surface/50"
				>
					<span class="text-6xl font-bold text-accent/20 font-serif">
						{loadedBook.book.title.charAt(0)}
					</span>
				</div>
			{/if}
			<div
				class="absolute inset-0 ring-1 ring-inset ring-white/10 pointer-events-none rounded-xl"
			></div>
		</div>

		<div class="w-full max-w-md flex flex-col gap-6 items-center mb-8">
			<div class="w-full px-2">
				<ProgressBar
					playbackMap={loadedBook.playbackMap}
					chapters={loadedBook.chapters}
					chunks={loadedBook.chunks}
					onSeek={handleSeek}
				/>
			</div>

			<div class="w-full flex justify-center">
				<Controls onSkip={handleSkip} />
			</div>
		</div>

		<div class="flex justify-center mb-8 relative z-20">
			<AskButton
				bookId={loadedBook.book.book_id}
				{recorder}
				onAnswerComplete={() => playback.play()}
			/>
		</div>

		<div
			class="w-full bg-surface/40 dark:bg-surface/20 backdrop-blur-xl border border-white/20 dark:border-white/5 rounded-3xl p-4 shadow-xl text-left transition-all"
		>
			<ChapterList
				chapters={loadedBook.chapters}
				{currentChapterId}
				chunks={loadedBook.chunks}
				onChapterSelect={handleChapterSelect}
			/>
		</div>
	</div>
</div>
