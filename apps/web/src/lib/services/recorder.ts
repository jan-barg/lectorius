/**
 * Push-to-talk audio recorder using MediaRecorder API.
 */

export class Recorder {
	private mediaRecorder: MediaRecorder | null = null;
	private chunks: Blob[] = [];
	private stream: MediaStream | null = null;

	async startRecording(): Promise<void> {
		const t0 = Date.now();
		console.log(`[recorder] Starting...`);

		this.chunks = [];
		this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
		console.log(`[recorder] getUserMedia: ${Date.now() - t0}ms`);

		this.mediaRecorder = new MediaRecorder(this.stream, {
			mimeType: 'audio/webm;codecs=opus'
		});
		console.log(`[recorder] MediaRecorder created: ${Date.now() - t0}ms`);

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
				this.cleanup();
				resolve(blob);
			};

			this.mediaRecorder.stop();
		});
	}

	cancelRecording(): void {
		if (this.mediaRecorder?.state === 'recording') {
			this.mediaRecorder.stop();
		}
		this.cleanup();
	}

	private cleanup(): void {
		this.stream?.getTracks().forEach((t) => t.stop());
		this.stream = null;
		this.mediaRecorder = null;
		this.chunks = [];
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
