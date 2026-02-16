/**
 * Push-to-talk audio recorder using MediaRecorder API.
 * Supports pre-acquiring the mic stream and MediaRecorder so startRecording() is near-instant.
 */

const MIME_TYPE = 'audio/webm;codecs=opus';

export class Recorder {
	private mediaRecorder: MediaRecorder | null = null;
	private warmRecorder: MediaRecorder | null = null;
	private chunks: Blob[] = [];
	private stream: MediaStream | null = null;

	/**
	 * Pre-acquire the mic stream. Call on a user gesture (e.g. first play press)
	 * so startRecording() doesn't need to wait for getUserMedia.
	 */
	async acquireStream(): Promise<void> {
		if (this.stream && this.isStreamAlive()) {
			console.log(`[recorder] Stream already acquired`);
			return;
		}

		const t0 = Date.now();
		console.log(`[recorder] Acquiring stream...`);
		this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
		console.log(`[recorder] Stream acquired: ${Date.now() - t0}ms`);
	}

	/**
	 * Check if the pre-acquired stream is still usable.
	 */
	private isStreamAlive(): boolean {
		if (!this.stream) return false;
		return this.stream.getAudioTracks().some((t) => t.readyState === 'live');
	}

	/**
	 * Warm up stream + MediaRecorder on hover/touch so startRecording() is instant.
	 * Fire-and-forget — errors are logged but not thrown.
	 */
	warmUp(): void {
		if (this.warmRecorder || this.mediaRecorder?.state === 'recording') return;

		const t0 = Date.now();
		console.log(`[recorder] Warming up...`);

		const doWarmUp = async () => {
			if (!this.stream || !this.isStreamAlive()) {
				this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
				console.log(`[recorder] Stream acquired: ${Date.now() - t0}ms`);
			}

			this.warmRecorder = new MediaRecorder(this.stream, { mimeType: MIME_TYPE });
			console.log(`[recorder] MediaRecorder pre-created: ${Date.now() - t0}ms`);
		};

		doWarmUp().catch((e) => {
			console.warn(`[recorder] Warm-up failed:`, e);
		});
	}

	async startRecording(): Promise<void> {
		const t0 = Date.now();
		console.log(`[recorder] Starting...`);

		this.chunks = [];

		// Use pre-warmed MediaRecorder if available
		if (this.warmRecorder && this.stream && this.isStreamAlive()) {
			console.log(`[recorder] Using warm MediaRecorder: ${Date.now() - t0}ms`);
			this.mediaRecorder = this.warmRecorder;
			this.warmRecorder = null;
		} else {
			// Fall back to full initialization
			this.warmRecorder = null;
			if (!this.stream || !this.isStreamAlive()) {
				console.log(`[recorder] No pre-acquired stream, acquiring now...`);
				this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
				console.log(`[recorder] getUserMedia (fallback): ${Date.now() - t0}ms`);
			} else {
				console.log(`[recorder] Using pre-acquired stream: ${Date.now() - t0}ms`);
			}

			this.mediaRecorder = new MediaRecorder(this.stream, { mimeType: MIME_TYPE });
			console.log(`[recorder] MediaRecorder created: ${Date.now() - t0}ms`);
		}

		this.mediaRecorder.ondataavailable = (e) => {
			if (e.data.size > 0) this.chunks.push(e.data);
		};

		return new Promise((resolve) => {
			this.mediaRecorder!.onstart = () => {
				console.log(`[recorder] Actually recording: ${Date.now() - t0}ms`);
				resolve();
			};
			this.mediaRecorder!.start();
		});
	}

	async stopRecording(): Promise<Blob> {
		const t0 = Date.now();
		console.log(`[recorder] Stopping...`);

		return new Promise((resolve, reject) => {
			if (!this.mediaRecorder) return reject(new Error('No recording'));

			this.mediaRecorder.onstop = () => {
				const blob = new Blob(this.chunks, { type: 'audio/webm' });
				console.log(`[recorder] Blob created: ${Date.now() - t0}ms, chunks: ${this.chunks.length}, size: ${blob.size} bytes`);
				// Only clean up the recorder, keep the stream for reuse
				this.mediaRecorder = null;
				this.chunks = [];
				resolve(blob);
			};

			this.mediaRecorder.stop();
		});
	}

	cancelRecording(): void {
		if (this.mediaRecorder?.state === 'recording') {
			this.mediaRecorder.stop();
		}
		this.mediaRecorder = null;
		this.warmRecorder = null;
		this.chunks = [];
		// Don't release the stream on cancel — keep it for next recording
	}

	/**
	 * Release the warm stream if the user left without clicking.
	 * Only releases if not currently recording.
	 */
	releaseWarmStream(): void {
		if (this.mediaRecorder?.state === 'recording') return;
		this.warmRecorder = null;
		this.stream?.getTracks().forEach((t) => t.stop());
		this.stream = null;
		console.log(`[recorder] Warm stream released`);
	}

	/**
	 * Release the mic stream. Call on page destroy/navigation.
	 */
	releaseStream(): void {
		this.cancelRecording();
		this.stream?.getTracks().forEach((t) => t.stop());
		this.stream = null;
		console.log(`[recorder] Stream released`);
	}
}

export async function blobToBase64(blob: Blob): Promise<string> {
	return new Promise((resolve, reject) => {
		const reader = new FileReader();
		reader.onloadend = () => resolve((reader.result as string).split(',')[1]);
		reader.onerror = reject;
		reader.readAsDataURL(blob);
	});
}
