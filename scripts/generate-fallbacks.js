const OpenAI = require('openai').default;
const fs = require('fs');
const path = require('path');

const openai = new OpenAI(); // Uses OPENAI_API_KEY from env

const fallbacks = [
  {
    id: 'no_context_yet',
    text: "I don't have enough context yet. Let's keep reading."
  },
  {
    id: 'book_only',
    text: "I can only help with questions about this book."
  },
  {
    id: 'error',
    text: "I can't seem to find an answer right now."
  }
];

async function generate() {
  const outputDir = path.join(__dirname, 'fallback-audio');
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  for (const f of fallbacks) {
    console.log(`Generating ${f.id}...`);
    const speech = await openai.audio.speech.create({
      model: 'tts-1',
      voice: 'alloy',
      input: f.text
    });
    const buffer = Buffer.from(await speech.arrayBuffer());
    const outputPath = path.join(outputDir, `${f.id}.mp3`);
    fs.writeFileSync(outputPath, buffer);
    console.log(`Created ${outputPath}`);
  }

  console.log('\nDone! Upload these files to Supabase: system/audio/');
}

generate().catch(console.error);
