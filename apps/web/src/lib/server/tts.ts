import { getOpenAI } from '$lib/server/clients';
import { env } from '$env/dynamic/private';

export type TTSProvider = 'openai' | 'elevenlabs';

const TTS_PROVIDER: TTSProvider = 'openai';

export async function generateSpeech(text: string): Promise<string> {
	const buffer =
		TTS_PROVIDER === 'openai' ? await generateOpenAI(text) : await generateElevenLabs(text);
	return buffer.toString('base64');
}

async function generateOpenAI(text: string): Promise<Buffer> {
	const speech = await getOpenAI().audio.speech.create({
		model: 'tts-1',
		voice: 'alloy',
		input: text
	});
	return Buffer.from(await speech.arrayBuffer());
}

async function generateElevenLabs(text: string): Promise<Buffer> {
	const voiceId = env.ELEVENLABS_VOICE_ID;
	const apiKey = env.ELEVENLABS_API_KEY;
	if (!voiceId || !apiKey) {
		throw new Error('Missing ELEVENLABS_VOICE_ID or ELEVENLABS_API_KEY');
	}

	const response = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${voiceId}`, {
		method: 'POST',
		headers: {
			'xi-api-key': apiKey,
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({
			text,
			model_id: 'eleven_turbo_v2',
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
