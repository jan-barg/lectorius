import { writable, get } from 'svelte/store';
import { browser } from '$app/environment';

const STORAGE_KEY = 'lectorius_music';

export interface Song {
	song_id: string;
	title: string;
	duration_ms: number;
	file_path: string;
}

export interface Playlist {
	playlist_id: string;
	name: string;
	type: 'general' | 'book';
	book_id: string | null;
	songs: Song[];
}

const FALLBACK_PLAYLISTS: Playlist[] = [
	{
		playlist_id: 'paris-jazz-cafe',
		name: 'Paris Jazz Cafe',
		type: 'general',
		book_id: null,
		songs: [
			{ song_id: '01', title: 'Café Morning', duration_ms: 240000, file_path: '' },
			{ song_id: '02', title: 'Midnight Stroll', duration_ms: 195000, file_path: '' },
			{ song_id: '03', title: 'Rainy Window', duration_ms: 210000, file_path: '' }
		]
	}
];

/** Reactive playlists store — populated from Supabase, falls back to hardcoded data */
export const playlists = writable<Playlist[]>(FALLBACK_PLAYLISTS);

/** Update a song's duration once audio metadata is known */
export function setSongDuration(playlistId: string, songIndex: number, durationMs: number): void {
	playlists.update((pls) =>
		pls.map((pl) => {
			if (pl.playlist_id !== playlistId) return pl;
			const songs = pl.songs.map((s, i) =>
				i === songIndex ? { ...s, duration_ms: durationMs } : s
			);
			return { ...pl, songs };
		})
	);
}

/** Fetch playlists from the server and update the store */
export async function fetchPlaylists(): Promise<void> {
	try {
		const res = await fetch('/api/music/playlists');
		if (!res.ok) return;
		const data = await res.json();
		if (data.playlists?.length > 0) {
			playlists.set(data.playlists);
		}
	} catch {
		// Keep fallback playlists
	}
}

export interface MusicState {
	current_playlist_id: string | null;
	current_song_index: number;
	current_time: number;
	volume: number; // 0-100 display value
	loop: boolean;
	is_playing: boolean;
}

const DEFAULT_STATE: MusicState = {
	current_playlist_id: FALLBACK_PLAYLISTS[0].playlist_id,
	current_song_index: 0,
	current_time: 0,
	volume: 70,
	loop: false,
	is_playing: false
};

function hydrate(): MusicState {
	if (!browser) return DEFAULT_STATE;
	try {
		const raw = localStorage.getItem(STORAGE_KEY);
		if (!raw) return DEFAULT_STATE;
		const saved = JSON.parse(raw);
		return {
			current_playlist_id: saved.current_playlist_id ?? null,
			current_song_index: saved.current_song_index ?? 0,
			current_time: saved.current_time ?? 0,
			volume: saved.volume ?? 70,
			loop: saved.loop ?? false,
			is_playing: false // never restore playing state
		};
	} catch {
		return DEFAULT_STATE;
	}
}

function persist(state: MusicState): void {
	if (!browser) return;
	try {
		localStorage.setItem(
			STORAGE_KEY,
			JSON.stringify({
				current_playlist_id: state.current_playlist_id,
				current_song_index: state.current_song_index,
				current_time: state.current_time,
				volume: state.volume,
				loop: state.loop
			})
		);
	} catch {
		// localStorage full or unavailable
	}
}

function createMusicStore() {
	const { subscribe, set, update } = writable<MusicState>(hydrate());

	function updateAndPersist(fn: (s: MusicState) => MusicState) {
		update((s) => {
			const next = fn(s);
			persist(next);
			return next;
		});
	}

	return {
		subscribe,
		play: () => updateAndPersist((s) => ({ ...s, is_playing: true })),
		pause: () => updateAndPersist((s) => ({ ...s, is_playing: false })),
		togglePlay: () => updateAndPersist((s) => ({ ...s, is_playing: !s.is_playing })),
		nextSong: (playlistLength: number) =>
			updateAndPersist((s) => {
				if (playlistLength === 0) return s;
				if (s.current_song_index < playlistLength - 1) {
					return { ...s, current_song_index: s.current_song_index + 1, current_time: 0 };
				}
				if (s.loop) {
					return { ...s, current_song_index: 0, current_time: 0 };
				}
				return { ...s, is_playing: false };
			}),
		prevSong: (currentTimeSeconds: number) =>
			updateAndPersist((s) => {
				if (currentTimeSeconds > 5) {
					return { ...s, current_time: 0 };
				}
				if (s.current_song_index > 0) {
					return { ...s, current_song_index: s.current_song_index - 1, current_time: 0 };
				}
				return { ...s, current_time: 0 };
			}),
		setVolume: (volume: number) =>
			updateAndPersist((s) => ({ ...s, volume: Math.max(0, Math.min(100, volume)) })),
		toggleLoop: () => updateAndPersist((s) => ({ ...s, loop: !s.loop })),
		setPlaylist: (playlistId: string) =>
			updateAndPersist((s) => ({
				...s,
				current_playlist_id: playlistId,
				current_song_index: 0,
				current_time: 0,
				is_playing: true
			})),
		setSong: (index: number) =>
			updateAndPersist((s) => ({
				...s,
				current_song_index: index,
				current_time: 0,
				is_playing: true
			})),
		/** Update current_time for display (no localStorage write — used by audio timeupdate) */
		updateTime: (time: number) => update((s) => ({ ...s, current_time: time })),
		/** Seek to a specific time and persist (used by user-initiated seeks) */
		seekTo: (time: number) => updateAndPersist((s) => ({ ...s, current_time: time })),
		reset: () => {
			const fresh = DEFAULT_STATE;
			persist(fresh);
			set(fresh);
		}
	};
}

export const music = createMusicStore();

/** Convert display volume (0-100) to actual audio volume (0-0.6) */
export function displayToActualVolume(displayVolume: number): number {
	return (displayVolume / 100) * 0.6;
}
