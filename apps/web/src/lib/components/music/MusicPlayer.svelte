<script lang="ts">
	import { music, playlists, setSongDuration } from '$lib/stores/music';
	import { playback } from '$lib/stores/playback';
	import { MusicAudioEngine } from '$lib/services/music-audio';
	import { toPerceptualVolume } from '$lib/utils/audio';
	import { fly } from 'svelte/transition';
	import { onMount, onDestroy } from 'svelte';
	import { get } from 'svelte/store';

	import PlaylistSelector from './PlaylistSelector.svelte';
	import MusicPlaylist from './MusicPlaylist.svelte';
	import MusicProgressBar from './MusicProgressBar.svelte';
	import MusicControls from './MusicControls.svelte';
	import MusicVolumeSlider from './MusicVolumeSlider.svelte';

	let expanded = false;
	let engine: MusicAudioEngine | null = null;
	let audioDurationMs = 0;
	let unsubscribeMusic: (() => void) | null = null;
	let unsubscribePlaylists: (() => void) | null = null;
	let unsubscribePlayback: (() => void) | null = null;

	$: playlist = $playlists.find((p) => p.playlist_id === $music.current_playlist_id) ?? null;
	$: songs = playlist?.songs ?? [];
	$: currentSong = songs[$music.current_song_index] ?? null;
	$: songName = currentSong?.title ?? 'No music selected';
	$: hasPlaylist = $music.current_playlist_id !== null;
	$: totalMs = audioDurationMs || (currentSong?.duration_ms ?? 0);
	$: elapsedMs = $music.current_time * 1000;

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

		let prevSongKey = '';
		let prevIsPlaying = false;
		let prevVolume = -1;
		let prevDucked = false;
		let songLoaded = false;

		unsubscribeMusic = music.subscribe((state) => {
			if (!engine) return;

			if (state.ducked !== prevDucked) {
				prevDucked = state.ducked;
				if (state.ducked) {
					engine.fadeTo(0, 300);
				} else {
					engine.fadeTo(toPerceptualVolume(state.volume, 0.6), 500);
				}
			}

			if (state.volume !== prevVolume) {
				prevVolume = state.volume;
				if (!state.ducked) engine.setVolume(state.volume);
			}

			const songKey = `${state.current_playlist_id}:${state.current_song_index}`;
			if (songKey !== prevSongKey) {
				prevSongKey = songKey;
				audioDurationMs = 0;
				songLoaded = false;

				const pl = get(playlists).find(
					(p) => p.playlist_id === state.current_playlist_id
				);
				const song = pl?.songs[state.current_song_index];

				if (song?.file_url) {
					engine.load(song.file_url, state.current_time);
					songLoaded = true;
					if (state.is_playing) engine.play();

					const nextSong = pl?.songs[state.current_song_index + 1];
					if (nextSong?.file_url) engine.preload(nextSong.file_url);
				}

				prevIsPlaying = state.is_playing;
				return;
			}

			if (state.is_playing !== prevIsPlaying) {
				prevIsPlaying = state.is_playing;
				if (state.is_playing) engine.play();
				else engine.pause();
			}
		});

		// Sync music play/pause with audiobook when enabled
		let prevBookPlaying: boolean | null = null;
		unsubscribePlayback = playback.subscribe((pbState) => {
			const musicState = get(music);
			if (!musicState.sync_with_book || musicState.ducked || !pbState.book_id) {
				prevBookPlaying = null;
				return;
			}
			if (prevBookPlaying === null) {
				prevBookPlaying = pbState.is_playing;
				return;
			}
			if (pbState.is_playing !== prevBookPlaying) {
				prevBookPlaying = pbState.is_playing;
				if (pbState.is_playing) music.play();
				else music.pause();
			}
		});

		// Probe song durations when playlists arrive
		unsubscribePlaylists = playlists.subscribe((allPlaylists) => {
			for (const pl of allPlaylists) {
				for (let i = 0; i < pl.songs.length; i++) {
					const s = pl.songs[i];
					if (s.file_url && s.duration_ms === 0) {
						const probe = new Audio();
						const idx = i;
						const plId = pl.playlist_id;
						probe.preload = 'metadata';
						probe.addEventListener('loadedmetadata', () => {
							if (probe.duration && isFinite(probe.duration)) {
								setSongDuration(plId, idx, Math.round(probe.duration * 1000));
							}
							probe.src = '';
						}, { once: true });
						probe.src = s.file_url;
					}
				}
			}

			// Load current song if not yet loaded (playlists arrived after hydrated music state)
			if (!songLoaded && engine) {
				const musicState = get(music);
				if (musicState.current_playlist_id) {
					const currentPl = allPlaylists.find(p => p.playlist_id === musicState.current_playlist_id);
					const currentSong = currentPl?.songs[musicState.current_song_index];
					if (currentSong?.file_url) {
						engine.load(currentSong.file_url, musicState.current_time);
						songLoaded = true;

						const nextSong = currentPl?.songs[musicState.current_song_index + 1];
						if (nextSong?.file_url) engine.preload(nextSong.file_url);
					}
				}
			}
		});
	});

	onDestroy(() => {
		unsubscribeMusic?.();
		unsubscribePlaylists?.();
		unsubscribePlayback?.();
		engine?.destroy();
		engine = null;
	});

	function handleVolumeInput(e: Event) {
		const target = e.target as HTMLInputElement;
		music.setVolume(parseInt(target.value, 10));
	}

	function handleSeek(timeSeconds: number) {
		music.seekTo(timeSeconds);
		engine?.seekTo(timeSeconds);
	}

	function handleSelectPlaylist(playlistId: string) {
		music.setPlaylist(playlistId);
	}

	function handleSelectSong(index: number) {
		music.setSong(index);
	}

	function handleRewind() {
		const prevIndex = $music.current_song_index;
		music.prevSong($music.current_time);
		if (get(music).current_song_index === prevIndex) {
			engine?.seekTo(0);
		}
	}

	function handleSkip() {
		music.nextSong(songs.length);
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
					<!-- Header -->
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

					<PlaylistSelector
						playlists={$playlists}
						currentPlaylistId={$music.current_playlist_id}
						onSelectPlaylist={handleSelectPlaylist}
					/>

					<p class="text-xs text-muted">
						Now playing: <span class="font-medium text-text">{songName}</span>
					</p>

					<MusicPlaylist
						{songs}
						currentSongIndex={$music.current_song_index}
						onSelectSong={handleSelectSong}
					/>

					<MusicProgressBar
						{elapsedMs}
						{totalMs}
						onSeek={handleSeek}
					/>

					<MusicControls
						isPlaying={$music.is_playing}
						isLooping={$music.loop}
						onPlay={() => music.play()}
						onPause={() => music.pause()}
						onSkip={handleSkip}
						onRewind={handleRewind}
						onToggleLoop={() => music.toggleLoop()}
					/>

					<MusicVolumeSlider volume={$music.volume} onVolumeInput={handleVolumeInput} />

					<button
						class="flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-sm transition-colors {$music.sync_with_book ? 'bg-accent/10 text-accent' : 'text-muted hover:bg-white/5 hover:text-text'}"
						onclick={() => music.toggleSync()}
					>
						<svg class="h-4 w-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101" />
							<path stroke-linecap="round" stroke-linejoin="round" d="M10.172 13.828a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.102 1.101" />
						</svg>
						<span class="font-medium">Sync with audiobook</span>
					</button>

					<p class="text-center text-[10px] text-muted/50">Generated with Eleven Music</p>
				</div>
			</div>
		{/if}

		<!-- Collapsed bar -->
		<div
			class="flex w-full sm:w-96 items-center gap-3 rounded-2xl border border-white/10 bg-surface/90 px-4 py-3.5 shadow-lg backdrop-blur-md"
		>
			<svg class="h-5 w-5 shrink-0 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
					d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2z"
				/>
			</svg>

			<span class="min-w-0 flex-1 truncate text-sm font-medium text-text">
				{songName}
			</span>

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

			<div class="hidden sm:flex">
				<MusicVolumeSlider volume={$music.volume} onVolumeInput={handleVolumeInput} compact />
			</div>

			<button
				class="rounded-full p-1.5 transition-colors {$music.sync_with_book ? 'text-accent' : 'text-muted hover:text-text'}"
				onclick={() => music.toggleSync()}
				aria-label={$music.sync_with_book ? 'Unsync from audiobook' : 'Sync with audiobook'}
				title={$music.sync_with_book ? 'Synced with audiobook' : 'Sync with audiobook'}
			>
				<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101" />
					<path stroke-linecap="round" stroke-linejoin="round" d="M10.172 13.828a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.102 1.101" />
				</svg>
			</button>

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
