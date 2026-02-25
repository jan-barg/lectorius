import { getOpenAI } from '$lib/server/clients';
import { env } from '$env/dynamic/private';

export type TTSProvider = 'openai' | 'elevenlabs';

interface TTSOptions {
	text: string;
	provider?: TTSProvider;
	voice_id?: string;
}

export async function generateSpeech(options: TTSOptions): Promise<string> {
	const { text, provider = 'openai', voice_id } = options;

	let buffer: Buffer;
	if (provider === 'elevenlabs' && voice_id) {
		buffer = await generateElevenLabs(text, voice_id);
	} else {
		buffer = await generateOpenAI(text, voice_id);
	}
	return buffer.toString('base64');
}

async function generateOpenAI(text: string, voice?: string): Promise<Buffer> {
	const speech = await getOpenAI().audio.speech.create({
		model: 'tts-1',
		voice: (voice as 'alloy' | 'echo' | 'fable' | 'onyx' | 'nova' | 'shimmer') || 'nova',
		input: text
	});
	return Buffer.from(await speech.arrayBuffer());
}

async function generateElevenLabs(text: string, voiceId: string): Promise<Buffer> {
	const apiKey = env.ELEVENLABS_API_KEY;
	if (!apiKey) {
		throw new Error('Missing ELEVENLABS_API_KEY');
	}

	const response = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${voiceId}`, {
		method: 'POST',
		headers: {
			'xi-api-key': apiKey,
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({
			text,
			model_id: 'eleven_flash_v2_5',
			voice_settings: {
				stability: 0.5,
				similarity_boost: 0.75
			}
		})
	});

	if (!response.ok) {
		throw new Error(`ElevenLabs error: ${response.status}`);
	}

	return Buffer.from(await response.arrayBuffer());
}
