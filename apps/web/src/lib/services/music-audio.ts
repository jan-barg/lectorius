import { toPerceptualVolume } from '$lib/utils/audio';

interface MusicAudioCallbacks {
	onTimeUpdate: (timeSeconds: number) => void;
	onSongEnd: () => void;
	onDurationKnown: (durationMs: number) => void;
}

export class MusicAudioEngine {
	private audio: HTMLAudioElement;
	private preloadAudio: HTMLAudioElement | null = null;
	private callbacks: MusicAudioCallbacks;
	private fadeInterval: ReturnType<typeof setInterval> | null = null;

	constructor(callbacks: MusicAudioCallbacks) {
		this.audio = new Audio();
		this.audio.preload = 'none';
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
		this.cancelFade();
		this.audio.volume = toPerceptualVolume(displayVolume, 0.6);
	}

	fadeTo(targetVolume: number, durationMs: number): void {
		this.cancelFade();
		const start = this.audio.volume;
		const diff = targetVolume - start;
		if (Math.abs(diff) < 0.001) {
			this.audio.volume = targetVolume;
			return;
		}
		const stepMs = 16;
		const steps = Math.ceil(durationMs / stepMs);
		let step = 0;
		this.fadeInterval = setInterval(() => {
			step++;
			if (step >= steps) {
				this.audio.volume = targetVolume;
				this.cancelFade();
				return;
			}
			this.audio.volume = start + diff * (step / steps);
		}, stepMs);
	}

	private cancelFade(): void {
		if (this.fadeInterval !== null) {
			clearInterval(this.fadeInterval);
			this.fadeInterval = null;
		}
	}

	preload(src: string): void {
		if (this.preloadAudio) {
			this.preloadAudio.src = '';
		}
		this.preloadAudio = new Audio();
		this.preloadAudio.preload = 'metadata';
		this.preloadAudio.src = src;
	}

	destroy(): void {
		this.cancelFade();
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
