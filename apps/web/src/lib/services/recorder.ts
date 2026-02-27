/**
 * Push-to-talk audio recorder using MediaRecorder API.
 * Supports pre-acquiring the mic stream and MediaRecorder so startRecording() is near-instant.
 */

const MIME_TYPE = 'audio/webm;codecs=opus';

export class Recorder {
	private mediaRecorder: MediaRecorder | null = null;
	private warmRecorder: MediaRecorder | null = null;
	private isWarming = false;
	private chunks: Blob[] = [];
	private stream: MediaStream | null = null;

	/**
	 * Pre-acquire the mic stream. Call on a user gesture (e.g. first play press)
	 * so startRecording() doesn't need to wait for getUserMedia.
	 */
	async acquireStream(): Promise<void> {
		if (this.stream && this.isStreamAlive()) {
			return;
		}

		this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
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
	 * Fire-and-forget — errors are silently ignored.
	 */
	warmUp(): void {
		if (this.warmRecorder || this.isWarming || this.mediaRecorder?.state === 'recording') return;

		this.isWarming = true;

		const doWarmUp = async () => {
			if (!this.stream || !this.isStreamAlive()) {
				this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
			}

			this.warmRecorder = new MediaRecorder(this.stream, { mimeType: MIME_TYPE });
		};

		doWarmUp().catch(() => {}).finally(() => { this.isWarming = false; });
	}

	async startRecording(): Promise<void> {
		this.chunks = [];

		// Use pre-warmed MediaRecorder if available
		if (this.warmRecorder && this.stream && this.isStreamAlive()) {
			this.mediaRecorder = this.warmRecorder;
			this.warmRecorder = null;
		} else {
			// Fall back to full initialization
			this.warmRecorder = null;
			if (!this.stream || !this.isStreamAlive()) {
				this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
			}

			this.mediaRecorder = new MediaRecorder(this.stream, { mimeType: MIME_TYPE });
		}

		this.mediaRecorder.ondataavailable = (e) => {
			if (e.data.size > 0) this.chunks.push(e.data);
		};

		return new Promise((resolve) => {
			this.mediaRecorder!.onstart = () => {
				resolve();
			};
			this.mediaRecorder!.start();
		});
	}

	async stopRecording(): Promise<Blob> {
		return new Promise((resolve, reject) => {
			if (!this.mediaRecorder) return reject(new Error('No recording'));

			this.mediaRecorder.onstop = () => {
				const blob = new Blob(this.chunks, { type: 'audio/webm' });
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
	}

	/**
	 * Release the mic stream. Call on page destroy/navigation.
	 */
	releaseStream(): void {
		this.cancelRecording();
		this.stream?.getTracks().forEach((t) => t.stop());
		this.stream = null;
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
