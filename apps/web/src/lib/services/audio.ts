import type { PlaybackMapEntry } from '$lib/types';

interface AudioEngineCallbacks {
	onChunkEnd: () => void;
	onTimeUpdate: (currentTimeMs: number) => void;
}

export class AudioEngine {
	private audio: HTMLAudioElement;
	private preloadAudio: HTMLAudioElement | null = null;
	private map: Map<number, PlaybackMapEntry>;
	private callbacks: AudioEngineCallbacks;
	private currentChunkIndex = 0;
	private speed = 1;

	constructor(playbackMap: PlaybackMapEntry[], callbacks: AudioEngineCallbacks) {
		this.audio = new Audio();
		this.audio.preload = 'auto';
		this.callbacks = callbacks;

		this.map = new Map();
		for (const entry of playbackMap) {
			this.map.set(entry.chunk_index, entry);
		}

		this.handleEnded = this.handleEnded.bind(this);
		this.handleTimeUpdate = this.handleTimeUpdate.bind(this);
		this.audio.addEventListener('ended', this.handleEnded);
		this.audio.addEventListener('timeupdate', this.handleTimeUpdate);
	}

	play(chunkIndex: number, seekMs?: number): void {
		const entry = this.map.get(chunkIndex);
		if (!entry) return;

		this.currentChunkIndex = chunkIndex;

		if (this.audio.src !== entry.audio_path) {
			this.audio.src = entry.audio_path;
		}

		if (seekMs !== undefined && seekMs > 0) {
			this.audio.currentTime = seekMs / 1000;
		} else if (this.audio.src !== entry.audio_path) {
			this.audio.currentTime = 0;
		}

		this.audio.playbackRate = this.speed;
		this.audio.play();
		this.preload(chunkIndex + 1);
	}

	resume(): void {
		this.audio.playbackRate = this.speed;
		this.audio.play();
	}

	pause(): void {
		this.audio.pause();
	}

	seekTo(ms: number): void {
		this.audio.currentTime = ms / 1000;
	}

	getCurrentTimeMs(): number {
		return Math.round(this.audio.currentTime * 1000);
	}

	getDurationMs(chunkIndex: number): number {
		return this.map.get(chunkIndex)?.duration_ms ?? 0;
	}

	setSpeed(rate: number): void {
		this.speed = rate;
		this.audio.playbackRate = rate;
	}

	destroy(): void {
		this.audio.pause();
		this.audio.removeEventListener('ended', this.handleEnded);
		this.audio.removeEventListener('timeupdate', this.handleTimeUpdate);
		this.audio.src = '';
		if (this.preloadAudio) {
			this.preloadAudio.src = '';
			this.preloadAudio = null;
		}
	}

	private handleEnded(): void {
		this.callbacks.onChunkEnd();
	}

	private handleTimeUpdate(): void {
		this.callbacks.onTimeUpdate(this.getCurrentTimeMs());
	}

	private preload(chunkIndex: number): void {
		const entry = this.map.get(chunkIndex);
		if (!entry) return;

		if (this.preloadAudio) {
			this.preloadAudio.src = '';
		}
		this.preloadAudio = new Audio();
		this.preloadAudio.preload = 'auto';
		this.preloadAudio.src = entry.audio_path;
	}
}
