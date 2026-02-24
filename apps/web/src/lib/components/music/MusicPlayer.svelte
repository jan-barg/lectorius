<script lang="ts">
	import { music, playlists, fetchPlaylists, setSongDuration, type Playlist } from '$lib/stores/music';
	import { MusicAudioEngine } from '$lib/services/music-audio';
	import { fly } from 'svelte/transition';
	import { onMount, onDestroy } from 'svelte';
	import { get } from 'svelte/store';

	let expanded = false;
	let playlistDropdownOpen = false;
	let engine: MusicAudioEngine | null = null;
	let audioDurationMs = 0;
	let unsubscribeMusic: (() => void) | null = null;

	$: playlist = $playlists.find((p) => p.playlist_id === $music.current_playlist_id) ?? null;
	$: songs = playlist?.songs ?? [];
	$: currentSong = songs[$music.current_song_index] ?? null;
	$: songName = currentSong?.title ?? 'No music selected';
	$: hasPlaylist = $music.current_playlist_id !== null;

	// Progress bar — prefer audio's actual duration over metadata
	$: totalMs = audioDurationMs || (currentSong?.duration_ms ?? 0);
	$: elapsedMs = $music.current_time * 1000;
	$: progress = totalMs > 0 ? Math.min((elapsedMs / totalMs) * 100, 100) : 0;

	onMount(() => {
		engine = new MusicAudioEngine({
			onTimeUpdate: (seconds) => {
				music.updateTime(seconds);
			},
			onSongEnd: () => {
				const pl = get(playlists).find(
					(p) => p.playlist_id === get(music).current_playlist_id
				);
				music.nextSong(pl?.songs.length ?? 0);
			},
			onDurationKnown: (ms) => {
				audioDurationMs = ms;
				const state = get(music);
				if (state.current_playlist_id) {
					setSongDuration(state.current_playlist_id, state.current_song_index, ms);
				}
			}
		});

		// Drive audio engine from store changes
		let prevSongKey = '';
		let prevIsPlaying = false;
		let prevVolume = -1;

		unsubscribeMusic = music.subscribe((state) => {
			if (!engine) return;

			// Volume
			if (state.volume !== prevVolume) {
				prevVolume = state.volume;
				engine.setVolume(state.volume);
			}

			// Song changed?
			const songKey = `${state.current_playlist_id}:${state.current_song_index}`;
			if (songKey !== prevSongKey) {
				prevSongKey = songKey;
				audioDurationMs = 0;

				const pl = get(playlists).find(
					(p) => p.playlist_id === state.current_playlist_id
				);
				const song = pl?.songs[state.current_song_index];

				if (song?.file_path) {
					engine.load(song.file_path, state.current_time);
					if (state.is_playing) engine.play();

					// Preload next song
					const nextSong = pl?.songs[state.current_song_index + 1];
					if (nextSong?.file_path) engine.preload(nextSong.file_path);
				}

				prevIsPlaying = state.is_playing;
				return;
			}

			// Play/pause changed?
			if (state.is_playing !== prevIsPlaying) {
				prevIsPlaying = state.is_playing;
				if (state.is_playing) engine.play();
				else engine.pause();
			}
		});

		// Fetch real playlists from Supabase, then load current song
		fetchPlaylists().then(() => {
			if (!engine) return;
			const state = get(music);
			const pl = get(playlists).find(
				(p) => p.playlist_id === state.current_playlist_id
			);
			const song = pl?.songs[state.current_song_index];
			if (song?.file_path) {
				engine.load(song.file_path, state.current_time);
				engine.setVolume(state.volume);
			}

			// Probe all songs for duration metadata
			const allPlaylists = get(playlists);
			for (const playlist of allPlaylists) {
				for (let i = 0; i < playlist.songs.length; i++) {
					const s = playlist.songs[i];
					if (s.file_path && s.duration_ms === 0) {
						const probe = new Audio();
						const idx = i;
						const plId = playlist.playlist_id;
						probe.preload = 'metadata';
						probe.addEventListener('loadedmetadata', () => {
							if (probe.duration && isFinite(probe.duration)) {
								setSongDuration(plId, idx, Math.round(probe.duration * 1000));
							}
							probe.src = '';
						}, { once: true });
						probe.src = s.file_path;
					}
				}
			}
		});
	});

	onDestroy(() => {
		unsubscribeMusic?.();
		engine?.destroy();
		engine = null;
	});

	function handleVolumeInput(e: Event) {
		const target = e.target as HTMLInputElement;
		music.setVolume(parseInt(target.value, 10));
	}

	function handleProgressClick(e: MouseEvent) {
		const bar = e.currentTarget as HTMLElement;
		const rect = bar.getBoundingClientRect();
		const pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
		const seekTimeSeconds = (pct * totalMs) / 1000;
		music.seekTo(seekTimeSeconds);
		engine?.seekTo(seekTimeSeconds);
	}

	function selectPlaylist(pl: Playlist) {
		music.setPlaylist(pl.playlist_id);
		playlistDropdownOpen = false;
	}

	function selectSong(index: number) {
		music.setSong(index);
	}

	function handleRewind() {
		const prevIndex = $music.current_song_index;
		music.prevSong($music.current_time);
		// If song didn't change, just seek to start of current song
		if (get(music).current_song_index === prevIndex) {
			engine?.seekTo(0);
		}
	}

	function handleSkip() {
		music.nextSong(songs.length);
	}

	function formatTime(ms: number): string {
		const totalSeconds = Math.max(0, Math.floor(ms / 1000));
		const minutes = Math.floor(totalSeconds / 60);
		const seconds = totalSeconds % 60;
		return `${minutes}:${seconds.toString().padStart(2, '0')}`;
	}
</script>

{#if hasPlaylist}
	<div class="fixed bottom-4 left-4 right-4 sm:right-auto z-30 flex flex-col items-stretch">
		<!-- Expanded panel -->
		{#if expanded}
			<div
				class="mb-2 w-full sm:w-96 rounded-2xl border border-white/10 bg-surface/95 shadow-xl backdrop-blur-md"
				transition:fly={{ y: 20, duration: 250 }}
			>
				<div class="p-6 space-y-5">
					<!-- Header: collapse button -->
					<div class="flex items-center justify-between">
						<span class="text-xs font-bold uppercase tracking-widest text-muted/70">Music</span>
						<button
							class="rounded-full p-1 text-muted transition-colors hover:text-text"
							onclick={() => (expanded = false)}
							aria-label="Collapse music player"
						>
							<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
							</svg>
						</button>
					</div>

					<!-- Playlist selector -->
					<div class="relative">
						<button
							class="flex w-full items-center justify-between rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-text transition-colors hover:bg-white/10"
							onclick={() => (playlistDropdownOpen = !playlistDropdownOpen)}
						>
							<span class="truncate font-medium">{playlist?.name ?? 'Select playlist'}</span>
							<svg class="h-4 w-4 shrink-0 text-muted transition-transform {playlistDropdownOpen ? 'rotate-180' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
							</svg>
						</button>

						{#if playlistDropdownOpen}
							<div class="absolute bottom-full left-0 mb-1 w-full rounded-xl border border-white/10 bg-surface shadow-xl overflow-hidden z-10">
								{#each $playlists as pl (pl.playlist_id)}
									<button
										class="flex w-full items-center px-4 py-2.5 text-sm transition-colors
											{pl.playlist_id === $music.current_playlist_id
												? 'bg-accent/15 text-text'
												: 'text-muted hover:bg-white/5 hover:text-text'}"
										onclick={() => selectPlaylist(pl)}
									>
										<span class="truncate">{pl.name}</span>
									</button>
								{/each}
							</div>
						{/if}
					</div>

					<!-- Now playing -->
					<p class="text-xs text-muted">
						Now playing: <span class="font-medium text-text">{songName}</span>
					</p>

					<!-- Song list -->
					<div class="max-h-44 space-y-1 overflow-y-auto pr-1 [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-white/10 hover:[&::-webkit-scrollbar-thumb]:bg-white/20">
						{#each songs as song, i (song.song_id)}
							<button
								class="group flex w-full items-center rounded-xl px-3 py-2.5 text-left text-sm transition-all duration-200
									{i === $music.current_song_index
										? 'bg-accent/15 border border-accent/20 text-text'
										: 'border border-transparent text-muted hover:bg-surface/50 hover:text-text hover:border-white/5'}"
								onclick={() => selectSong(i)}
							>
								<span class="mr-3 w-5 text-right text-xs font-bold {i === $music.current_song_index ? 'text-accent' : 'text-muted/40'}">
									{i + 1}.
								</span>
								<span class="flex-1 truncate font-medium">{song.title}</span>
								<span class="ml-2 text-xs text-muted/60">{formatTime(song.duration_ms)}</span>
							</button>
						{/each}
					</div>

					<!-- Progress bar -->
					<div class="w-full group">
						<div
							class="relative h-[4px] w-full cursor-pointer overflow-visible rounded-full bg-muted/30 py-2 bg-clip-content"
							onclick={handleProgressClick}
							onkeydown={() => {}}
							role="slider"
							aria-valuemin={0}
							aria-valuemax={totalMs}
							aria-valuenow={elapsedMs}
							aria-label="Seek through song"
							tabindex="0"
						>
							<div
								class="absolute left-0 top-1/2 -translate-y-1/2 h-[4px] rounded-full bg-accent shadow-[0_0_12px_rgba(var(--color-accent),0.8)] transition-[width] duration-150"
								style="width: {progress}%"
							>
								<div class="absolute right-0 top-1/2 -translate-y-1/2 translate-x-1/2 w-2.5 h-2.5 bg-white rounded-full shadow-md scale-50 opacity-0 transition-all duration-200 group-hover:scale-100 group-hover:opacity-100 pointer-events-none"></div>
							</div>
						</div>
						<div class="mt-2 flex justify-between text-[10px] font-medium tracking-wide text-muted pointer-events-none">
							<span>{formatTime(elapsedMs)}</span>
							<span>{formatTime(totalMs)}</span>
						</div>
					</div>

					<!-- Controls row -->
					<div class="flex items-center justify-center gap-4">
						<!-- Rewind -->
						<button
							class="flex h-10 w-10 items-center justify-center rounded-full text-muted transition-all hover:bg-white/10 hover:text-text active:scale-95"
							onclick={handleRewind}
							aria-label="Previous song"
						>
							<svg class="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
								<path d="M6 6h2v12H6zm3.5 6l8.5 6V6z" />
							</svg>
						</button>

						<!-- Play/Pause -->
						<button
							class="flex h-12 w-12 items-center justify-center rounded-full bg-accent text-white shadow-[0_0_16px_rgba(var(--color-accent),0.4)] transition-all hover:bg-accent/80 hover:scale-105 active:scale-95"
							onclick={() => music.togglePlay()}
							aria-label={$music.is_playing ? 'Pause' : 'Play'}
						>
							{#if $music.is_playing}
								<svg class="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
									<path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z" />
								</svg>
							{:else}
								<svg class="h-5 w-5 ml-0.5" fill="currentColor" viewBox="0 0 24 24">
									<path d="M8 5v14l11-7z" />
								</svg>
							{/if}
						</button>

						<!-- Skip -->
						<button
							class="flex h-10 w-10 items-center justify-center rounded-full text-muted transition-all hover:bg-white/10 hover:text-text active:scale-95"
							onclick={handleSkip}
							aria-label="Next song"
						>
							<svg class="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
								<path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z" />
							</svg>
						</button>

						<!-- Loop -->
						<button
							class="flex h-10 w-10 items-center justify-center rounded-full transition-all active:scale-95
								{$music.loop
									? 'text-accent bg-accent/15 hover:bg-accent/25'
									: 'text-muted hover:bg-white/10 hover:text-text'}"
							onclick={() => music.toggleLoop()}
							aria-label="Toggle loop"
						>
							<svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" d="M17 1l4 4-4 4" />
								<path stroke-linecap="round" stroke-linejoin="round" d="M3 11V9a4 4 0 014-4h14" />
								<path stroke-linecap="round" stroke-linejoin="round" d="M7 23l-4-4 4-4" />
								<path stroke-linecap="round" stroke-linejoin="round" d="M21 13v2a4 4 0 01-4 4H3" />
							</svg>
						</button>
					</div>

					<!-- Volume -->
					<div class="flex items-center gap-2">
						<svg class="h-4 w-4 shrink-0 text-muted" fill="currentColor" viewBox="0 0 24 24">
							<path d="M11 5L6 9H2v6h4l5 4V5zm2 3.17v7.66a6.5 6.5 0 000-7.66z" />
						</svg>
						<input
							type="range"
							min="0"
							max="100"
							value={$music.volume}
							oninput={handleVolumeInput}
							class="music-volume-slider h-1 flex-1 cursor-pointer appearance-none rounded-full bg-white/10"
						/>
						<span class="w-8 text-right text-[10px] font-medium text-muted">{$music.volume}%</span>
					</div>

					<!-- Attribution -->
					<p class="text-center text-[10px] text-muted/50">Generated with ElevenLabs Music</p>
				</div>
			</div>
		{/if}

		<!-- Collapsed bar -->
		<div
			class="flex w-full sm:w-96 items-center gap-3 rounded-2xl border border-white/10 bg-surface/90 px-4 py-3.5 shadow-lg backdrop-blur-md"
		>
			<!-- Music icon -->
			<svg class="h-5 w-5 shrink-0 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
					d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2z"
				/>
			</svg>

			<!-- Song name -->
			<span class="min-w-0 flex-1 truncate text-sm font-medium text-text">
				{songName}
			</span>

			<!-- Play/Pause -->
			<button
				class="rounded-full p-1.5 text-text transition-colors hover:bg-white/10"
				onclick={() => music.togglePlay()}
				aria-label={$music.is_playing ? 'Pause' : 'Play'}
			>
				{#if $music.is_playing}
					<svg class="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
						<rect x="6" y="4" width="4" height="16" rx="1" />
						<rect x="14" y="4" width="4" height="16" rx="1" />
					</svg>
				{:else}
					<svg class="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
						<path d="M8 5v14l11-7z" />
					</svg>
				{/if}
			</button>

			<!-- Volume slider (hidden on mobile to save space) -->
			<div class="hidden sm:flex items-center gap-1.5">
				<svg class="h-3.5 w-3.5 shrink-0 text-muted" fill="currentColor" viewBox="0 0 24 24">
					<path d="M11 5L6 9H2v6h4l5 4V5zm2 3.17v7.66a6.5 6.5 0 000-7.66z" />
				</svg>
				<input
					type="range"
					min="0"
					max="100"
					value={$music.volume}
					oninput={handleVolumeInput}
					class="music-volume-slider h-1 w-16 cursor-pointer appearance-none rounded-full bg-white/10"
				/>
			</div>

			<!-- Expand/Collapse button -->
			<button
				class="rounded-full p-1 text-muted transition-colors hover:text-text"
				onclick={() => (expanded = !expanded)}
				aria-label={expanded ? 'Collapse music player' : 'Expand music player'}
			>
				<svg class="h-4 w-4 transition-transform duration-200 {expanded ? 'rotate-180' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" />
				</svg>
			</button>
		</div>
	</div>
{/if}

<!-- Close playlist dropdown on outside click -->
{#if playlistDropdownOpen}
	<button
		class="fixed inset-0 z-20"
		onclick={() => (playlistDropdownOpen = false)}
		aria-label="Close dropdown"
	></button>
{/if}

<style>
	.music-volume-slider::-webkit-slider-thumb {
		-webkit-appearance: none;
		appearance: none;
		width: 12px;
		height: 12px;
		border-radius: 50%;
		background: rgb(var(--color-accent));
		cursor: pointer;
	}
	.music-volume-slider::-moz-range-thumb {
		width: 12px;
		height: 12px;
		border-radius: 50%;
		border: none;
		background: rgb(var(--color-accent));
		cursor: pointer;
	}
	.music-volume-slider::-webkit-slider-runnable-track {
		height: 4px;
		border-radius: 2px;
	}
	.music-volume-slider::-moz-range-track {
		height: 4px;
		border-radius: 2px;
		background: rgba(255, 255, 255, 0.1);
	}
</style>
