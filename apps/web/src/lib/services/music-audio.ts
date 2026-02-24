import { displayToActualVolume } from '$lib/stores/music';

interface MusicAudioCallbacks {
	onTimeUpdate: (timeSeconds: number) => void;
	onSongEnd: () => void;
	onDurationKnown: (durationMs: number) => void;
}

export class MusicAudioEngine {
	private audio: HTMLAudioElement;
	private preloadAudio: HTMLAudioElement | null = null;
	private callbacks: MusicAudioCallbacks;

	constructor(callbacks: MusicAudioCallbacks) {
		this.audio = new Audio();
		this.audio.preload = 'auto';
		this.callbacks = callbacks;

		this.audio.addEventListener('ended', this.handleEnded);
		this.audio.addEventListener('timeupdate', this.handleTimeUpdate);
		this.audio.addEventListener('loadedmetadata', this.handleLoadedMetadata);
	}

	load(src: string, startTimeSeconds: number = 0): void {
		this.audio.src = src;
		this.audio.currentTime = startTimeSeconds;
	}

	play(): void {
		this.audio.play().catch(() => {});
	}

	pause(): void {
		this.audio.pause();
	}

	seekTo(timeSeconds: number): void {
		this.audio.currentTime = timeSeconds;
	}

	setVolume(displayVolume: number): void {
		this.audio.volume = displayToActualVolume(displayVolume);
	}

	preload(src: string): void {
		if (this.preloadAudio) {
			this.preloadAudio.src = '';
		}
		this.preloadAudio = new Audio();
		this.preloadAudio.preload = 'auto';
		this.preloadAudio.src = src;
	}

	destroy(): void {
		this.audio.pause();
		this.audio.removeEventListener('ended', this.handleEnded);
		this.audio.removeEventListener('timeupdate', this.handleTimeUpdate);
		this.audio.removeEventListener('loadedmetadata', this.handleLoadedMetadata);
		this.audio.src = '';
		if (this.preloadAudio) {
			this.preloadAudio.src = '';
			this.preloadAudio = null;
		}
	}

	private handleEnded = (): void => {
		this.callbacks.onSongEnd();
	};

	private handleTimeUpdate = (): void => {
		this.callbacks.onTimeUpdate(this.audio.currentTime);
	};

	private handleLoadedMetadata = (): void => {
		if (this.audio.duration && isFinite(this.audio.duration)) {
			this.callbacks.onDurationKnown(Math.round(this.audio.duration * 1000));
		}
	};
}
