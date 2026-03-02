<script lang="ts">
	import { onMount } from 'svelte';

	let visible: Record<string, boolean> = {};

	/* ─── QA Demo state ─── */
	const qaPairs = [
		{
			q: 'Why does Gatsby throw such lavish parties?',
			a: 'He hopes Daisy will wander in one evening — they live just across the bay.'
		},
		{
			q: 'Is Mr Darcy actually rude, or just shy?',
			a: 'Shy. He admits he struggles in company with people he doesn\'t know.'
		},
		{
			q: 'What happened to Gregor Samsa?',
			a: 'He woke one morning transformed into a giant insect. Kafka never explains why.'
		},
		{
			q: 'Why does Atticus defend Tom Robinson?',
			a: 'He believes in justice regardless of race — even when the whole town turns against him.'
		}
	];

	type Phase = 'reading' | 'cursor-in' | 'listening' | 'thinking' | 'speaking';
	let phase: Phase = 'reading';
	let qaIndex = 0;
	let showQuestion = false;
	let showAnswer = false;
	let cursorPressed = false;

	$: currentQA = qaPairs[qaIndex];

	function runCycle() {
		// Reset
		phase = 'reading';
		showQuestion = false;
		showAnswer = false;
		cursorPressed = false;

		// 0.8s — cursor slides in
		setTimeout(() => { phase = 'cursor-in'; }, 800);

		// 1.4s — cursor presses, button → listening
		setTimeout(() => { cursorPressed = true; phase = 'listening'; }, 1400);

		// 2.0s — question slides in
		setTimeout(() => { showQuestion = true; }, 2000);

		// 4.0s — cursor releases → thinking
		setTimeout(() => { cursorPressed = false; phase = 'thinking'; }, 4000);

		// 5.2s — speaking + answer slides in
		setTimeout(() => { phase = 'speaking'; }, 5200);
		setTimeout(() => { showAnswer = true; }, 5600);

		// 8.2s — everything winds down together: bubbles fade, cursor leaves, button returns to idle
		setTimeout(() => {
			showQuestion = false;
			showAnswer = false;
			phase = 'reading';
		}, 8200);

		// 10s — next cycle
		setTimeout(() => {
			qaIndex = (qaIndex + 1) % qaPairs.length;
			runCycle();
		}, 10000);
	}

	onMount(() => {
		// Scroll reveal observer
		const observer = new IntersectionObserver(
			(entries) => {
				for (const entry of entries) {
					if (entry.isIntersecting) {
						visible[entry.target.id] = true;
						observer.unobserve(entry.target);
					}
				}
			},
			{ threshold: 0.15 }
		);
		const sections = document.querySelectorAll('[data-reveal]');
		for (const section of sections) observer.observe(section);

		// Start demo loop
		runCycle();

		return () => observer.disconnect();
	});

	const techStack = [
		{ name: 'SvelteKit', color: '#FF3E00' },
		{ name: 'TypeScript', color: '#3178C6' },
		{ name: 'Python', color: '#F7D44F' },
		{ name: 'Claude', color: '#D4A27F' },
		{ name: 'ElevenLabs', color: '#FFFFFF' },
		{ name: 'Supabase', color: '#3ECF8E' },
		{ name: 'pgvector', color: '#336791' },
		{ name: 'Tailwind', color: '#38BDF8' },
	];
</script>

<svelte:head>
	<title>Lectorius — Books that talk back</title>
	<meta name="description" content="Listen to books narrated by AI voices matched to each story's era and tone. Ask questions, get spoiler-free answers. Literature, reimagined." />
</svelte:head>

<div class="dark">
<div class="landing-page grain-overlay relative min-h-screen bg-[#0A0908] text-[#F2EEE8] overflow-x-hidden">

	<!-- ═══════════════════════════════════════ HERO ═══════════════════════════════════════ -->
	<section class="relative min-h-screen flex flex-col overflow-hidden">
		<!-- Ambient glows -->
		<div class="pointer-events-none absolute top-[-200px] left-[-100px] h-[600px] w-[600px] rounded-full bg-[#DCA072]/[0.06] blur-[180px]"></div>
		<div class="pointer-events-none absolute bottom-[-100px] right-[-150px] h-[500px] w-[500px] rounded-full bg-[#BC6A34]/[0.04] blur-[160px]"></div>

		<!-- Giant title at top -->
		<div class="w-full px-4 sm:px-6 pt-12 sm:pt-16 md:pt-20 animate-fade-in-up stagger-1">
			<h1 class="hero-title font-display italic tracking-[-0.04em] leading-[0.82] text-center select-none">
				Lectorius
			</h1>
		</div>

		<!-- Two-column content -->
		<div class="flex-1 flex items-center w-full max-w-7xl mx-auto px-6 sm:px-10 lg:px-16 pb-16 md:pb-24">
			<div class="flex flex-col lg:flex-row items-center gap-14 lg:gap-10 xl:gap-20 w-full">

				<!-- Left: Copy -->
				<div class="flex-1 z-10 text-center lg:text-left">
					<h2 class="font-display leading-[0.98] tracking-[-0.03em] animate-fade-in-up stagger-2">
						<span class="block text-6xl sm:text-7xl md:text-8xl lg:text-[6.5rem] xl:text-[7.5rem] font-light text-[#F2EEE8]">Books that</span>
						<span class="block text-6xl sm:text-7xl md:text-8xl lg:text-[6.5rem] xl:text-[7.5rem] font-light italic text-[#DCA072]">talk back.</span>
					</h2>
					<p class="mt-8 md:mt-10 text-[#F2EEE8]/50 font-sans text-lg sm:text-xl md:text-2xl leading-relaxed max-w-xl mx-auto lg:mx-0 animate-fade-in-up stagger-3">
						Listen to classic literature narrated by AI voices matched to each story's era and tone. Then ask anything — spoiler-free.
					</p>
					<div class="mt-12 md:mt-14 animate-fade-in-up stagger-4">
						<a
							href="/library"
							class="group inline-flex items-center gap-5 rounded-2xl bg-[#DCA072] px-14 py-6 text-lg md:text-xl font-bold text-[#0A0908] shadow-xl shadow-[#DCA072]/20 transition-all duration-300 hover:brightness-110 hover:shadow-2xl hover:shadow-[#DCA072]/30 hover:translate-y-[-2px]"
						>
							Try it now
							<svg class="h-6 w-6 transition-transform duration-300 group-hover:translate-x-2" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
							</svg>
						</a>
					</div>
				</div>

				<!-- Right: QA Demo animation -->
				<div class="flex-1 flex justify-center items-center relative animate-fade-in-up stagger-3 w-full">
					<div class="demo-scene relative w-full max-w-[520px] h-[400px] sm:h-[440px] lg:h-[480px]">
						<!-- Question bubble (slides in from left) -->
						<div
							class="absolute left-0 right-12 sm:right-20 transition-all duration-700 ease-in-out"
							style="top: 12%; {showQuestion ? 'opacity: 1; transform: translateX(0);' : 'opacity: 0; transform: translateX(-30px);'}"
						>
							<div class="rounded-2xl rounded-bl-sm border border-[#F2EEE8]/[0.07] bg-[#161310] px-6 py-4 shadow-lg shadow-black/20">
								<p class="font-sans text-base sm:text-lg text-[#F2EEE8]/80 leading-relaxed">{currentQA.q}</p>
							</div>
						</div>

						<!-- The Button -->
						<div class="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2">
							<!-- Idle glow rings -->
							{#if phase === 'reading' || phase === 'cursor-in'}
								<div class="absolute inset-0 -m-4 rounded-full bg-[#DCA072]/10 animate-soft-ping"></div>
								<div class="absolute inset-0 -m-2 rounded-full bg-[#DCA072]/5 animate-glow-pulse"></div>
							{/if}

							<!-- Button itself -->
							<button
								class="demo-btn relative flex items-center justify-center gap-3 w-56 sm:w-60 px-8 py-4 rounded-full text-base font-semibold tracking-wide select-none {
									phase === 'listening' ? 'demo-btn-listening' :
									phase === 'thinking' ? 'demo-btn-thinking' :
									phase === 'speaking' ? 'demo-btn-speaking' :
									'demo-btn-idle'
								}"
								class:scale-95={cursorPressed}
								tabindex="-1"
							>
								<!-- Icon per state -->
								{#if phase === 'reading' || phase === 'cursor-in'}
									<svg class="h-5 w-5 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" d="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 01-3-3V4.5a3 3 0 116 0v8.25a3 3 0 01-3 3z" />
									</svg>
								{:else if phase === 'listening'}
									<span class="w-3 h-3 rounded-full bg-[#0A0908]/60 flex-shrink-0 recording-dot"></span>
								{:else if phase === 'thinking'}
									<svg class="h-5 w-5 flex-shrink-0 animate-spin" viewBox="0 0 24 24" fill="none">
										<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" opacity="0.2" />
										<path d="M12 2a10 10 0 019.95 9" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
									</svg>
								{:else if phase === 'speaking'}
									<span class="flex items-center gap-[3px] flex-shrink-0 h-5">
										<span class="wave-bar-mini" style="animation-delay: -0.2s; animation-duration: 0.7s;"></span>
										<span class="wave-bar-mini" style="animation-delay: -0.4s; animation-duration: 1.0s;"></span>
										<span class="wave-bar-mini" style="animation-delay: -0.1s; animation-duration: 0.6s;"></span>
										<span class="wave-bar-mini" style="animation-delay: -0.3s; animation-duration: 0.8s;"></span>
									</span>
								{/if}

								{#if phase === 'reading' || phase === 'cursor-in'}
									Hold to Ask
								{:else if phase === 'listening'}
									Listening...
								{:else if phase === 'thinking'}
									Thinking...
								{:else if phase === 'speaking'}
									Speaking...
								{/if}
							</button>
						</div>

						<!-- Fake cursor -->
						<div
							class="demo-cursor absolute pointer-events-none z-20"
							class:cursor-visible={phase !== 'reading'}
							class:cursor-pressed={cursorPressed}
							style="
								left: calc(50% + 24px);
								top: calc(50% + 16px);
							"
						>
							<svg width="24" height="28" viewBox="0 0 20 24" fill="none">
								<path d="M1 1L1 17.5L5.5 13.5L9.5 22L13 20.5L9 12H15L1 1Z" fill="#F2EEE8" stroke="#0A0908" stroke-width="1.5" stroke-linejoin="round"/>
							</svg>
						</div>

						<!-- Answer bubble (slides in from right) -->
						<div
							class="absolute left-12 sm:left-20 right-0 transition-all duration-700 ease-in-out"
							style="bottom: 8%; {showAnswer ? 'opacity: 1; transform: translateX(0);' : 'opacity: 0; transform: translateX(30px);'}"
						>
							<div class="rounded-2xl rounded-br-sm border border-[#DCA072]/15 bg-[#1A1610] px-6 py-4 shadow-lg shadow-black/20">
								<p class="font-sans text-base sm:text-lg text-[#DCA072]/80 leading-relaxed">{currentQA.a}</p>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>

		<!-- Scroll indicator -->
		<div class="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 animate-fade-in-up stagger-5">
			<span class="text-[#746950] text-xs font-sans tracking-widest uppercase">Scroll</span>
			<div class="scroll-line w-px h-8 bg-gradient-to-b from-[#746950] to-transparent"></div>
		</div>
	</section>

	<!-- ═══════════════════════════════════════ HOW IT WORKS ═══════════════════════════════ -->
	<section id="how-it-works" data-reveal class="py-28 md:py-36 relative">
		<div class="pointer-events-none absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-[#DCA072]/20 to-transparent"></div>

		<div class="max-w-5xl mx-auto px-6 sm:px-10">
			<div class="text-center mb-20 transition-all duration-1000 {visible['how-it-works'] ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}">
				<p class="text-[#DCA072] font-sans text-xs tracking-[0.35em] uppercase font-semibold mb-4">How it works</p>
				<h2 class="font-display text-4xl md:text-5xl font-light tracking-[-0.02em]">Three steps to a living book</h2>
			</div>

			<div class="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-10">
				{#each [
					{
						step: '01',
						title: 'Pick a book',
						desc: 'Browse the library of classic literature, each with its own voice and atmosphere.',
						icon: 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253'
					},
					{
						step: '02',
						title: 'Listen',
						desc: 'AI narration matched to each book\'s era and tone, with ambient music to set the scene.',
						icon: 'M19.114 5.636a9 9 0 010 12.728M16.463 8.288a5.25 5.25 0 010 7.424M6.75 8.25l4.72-4.72a.75.75 0 011.28.53v15.88a.75.75 0 01-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.009 9.009 0 012.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75z'
					},
					{
						step: '03',
						title: 'Ask anything',
						desc: 'Push to talk and get spoiler-free, accurate answers grounded in the text.',
						icon: 'M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 01.865-.501 48.172 48.172 0 003.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z'
					}
				] as step, i}
					<div
						class="group relative rounded-2xl border border-[#F2EEE8]/[0.05] bg-[#161310]/60 p-8 md:p-10 transition-all duration-700 hover:border-[#DCA072]/20 hover:bg-[#161310]"
						style="transition-delay: {visible['how-it-works'] ? i * 150 : 0}ms; opacity: {visible['how-it-works'] ? 1 : 0}; transform: translateY({visible['how-it-works'] ? 0 : 30}px);"
					>
						<div class="flex items-start gap-5 mb-5">
							<span class="text-[#DCA072]/30 font-display text-3xl font-light italic">{step.step}</span>
							<div class="mt-1.5 flex h-10 w-10 items-center justify-center rounded-xl bg-[#DCA072]/[0.08] text-[#DCA072] transition-colors duration-300 group-hover:bg-[#DCA072]/[0.12]">
								<svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" d={step.icon} />
								</svg>
							</div>
						</div>
						<h3 class="font-display text-2xl font-light tracking-tight mb-3 text-[#F2EEE8]">{step.title}</h3>
						<p class="text-sm text-[#F2EEE8]/40 leading-relaxed font-sans">{step.desc}</p>
					</div>
				{/each}
			</div>
		</div>
	</section>

	<!-- ═══════════════════════════════════════ FEATURES ════════════════════════════════════ -->
	<section id="features" data-reveal class="py-28 md:py-36 relative">
		<div class="pointer-events-none absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-[#F2EEE8]/[0.06] to-transparent"></div>

		<div class="max-w-5xl mx-auto px-6 sm:px-10">
			<div class="text-center mb-20 transition-all duration-1000 {visible['features'] ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}">
				<p class="text-[#DCA072] font-sans text-xs tracking-[0.35em] uppercase font-semibold mb-4">Features</p>
				<h2 class="font-display text-4xl md:text-5xl font-light tracking-[-0.02em]">Literature, reimagined</h2>
			</div>

			<div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
				{#each [
					{
						title: 'Push-to-talk Q&A',
						desc: 'Hold to ask, release to hear. Spoiler-aware AI that only references what you\'ve read so far.',
						icon: 'M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 01-3-3V4.5a3 3 0 116 0v8.25a3 3 0 01-3 3z',
						accent: '#DCA072'
					},
					{
						title: 'Era-matched voices',
						desc: 'Each book is narrated by an AI voice chosen to match its time period, geography, and narrative tone.',
						icon: 'M9.348 14.652a3.75 3.75 0 010-5.304m5.304 0a3.75 3.75 0 010 5.304m-7.425 2.121a6.75 6.75 0 010-9.546m9.546 0a6.75 6.75 0 010 9.546M5.106 18.894c-3.808-3.807-3.808-9.98 0-13.788m13.788 0c3.808 3.807 3.808 9.98 0 13.788M12 12h.008v.008H12V12zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z',
						accent: '#BC6A34'
					},
					{
						title: 'Ambient soundscapes',
						desc: 'Book-themed music and atmospheric audio that evolves with the story, drawing you deeper into the world.',
						icon: 'M9 9l10.5-3m0 6.553v3.75a2.25 2.25 0 01-1.632 2.163l-1.32.377a1.803 1.803 0 11-.99-3.467l2.31-.66a2.25 2.25 0 001.632-2.163zm0 0V2.25L9 5.25v10.303m0 0v3.75a2.25 2.25 0 01-1.632 2.163l-1.32.377a1.803 1.803 0 01-.99-3.467l2.31-.66A2.25 2.25 0 009 15.553z',
						accent: '#D4A27F'
					},
					{
						title: 'Reading progress',
						desc: 'Pick up right where you left off. Your position, preferences, and history are saved locally.',
						icon: 'M3 3v1.5M3 21v-6m0 0l2.77-.693a9 9 0 016.208.682l.108.054a9 9 0 006.086.71l3.114-.732a48.524 48.524 0 01-.005-10.499l-3.11.732a9 9 0 01-6.085-.711l-.108-.054a9 9 0 00-6.208-.682L3 4.5M3 15V4.5',
						accent: '#F2EEE8'
					}
				] as feature, i}
					<div
						class="group relative rounded-2xl border border-[#F2EEE8]/[0.05] bg-[#161310]/40 p-8 transition-all duration-700 hover:border-[#DCA072]/15 hover:bg-[#161310]/70"
						style="transition-delay: {visible['features'] ? i * 120 : 0}ms; opacity: {visible['features'] ? 1 : 0}; transform: translateY({visible['features'] ? 0 : 30}px);"
					>
						<div class="mb-5 flex h-11 w-11 items-center justify-center rounded-xl bg-[#F2EEE8]/[0.04] transition-colors duration-300 group-hover:bg-[#DCA072]/[0.1]">
							<svg class="h-5 w-5" style="color: {feature.accent}" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" d={feature.icon} />
							</svg>
						</div>
						<h3 class="font-display text-xl font-light tracking-tight mb-2 text-[#F2EEE8]">{feature.title}</h3>
						<p class="text-sm text-[#F2EEE8]/40 leading-relaxed font-sans">{feature.desc}</p>
					</div>
				{/each}
			</div>
		</div>
	</section>

	<!-- ═══════════════════════════════════════ TECH STACK ═════════════════════════════════ -->
	<section id="tech-stack" data-reveal class="py-28 md:py-36 relative">
		<div class="pointer-events-none absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-[#F2EEE8]/[0.06] to-transparent"></div>

		<div class="max-w-4xl mx-auto px-6 sm:px-10">
			<div class="text-center mb-16 transition-all duration-1000 {visible['tech-stack'] ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}">
				<p class="text-[#DCA072] font-sans text-xs tracking-[0.35em] uppercase font-semibold mb-4">Built with</p>
				<h2 class="font-display text-4xl md:text-5xl font-light tracking-[-0.02em]">The stack</h2>
			</div>

			<div class="flex flex-wrap justify-center gap-3 md:gap-4">
				{#each techStack as tech, i}
					<div
						class="rounded-xl border border-[#F2EEE8]/[0.06] bg-[#161310]/60 px-5 py-3 font-sans text-sm font-medium text-[#F2EEE8]/70 transition-all duration-500 hover:border-[#DCA072]/20 hover:text-[#F2EEE8]/90"
						style="transition-delay: {visible['tech-stack'] ? i * 70 : 0}ms; opacity: {visible['tech-stack'] ? 1 : 0}; transform: translateY({visible['tech-stack'] ? 0 : 20}px);"
					>
						<span class="inline-block w-2 h-2 rounded-full mr-2.5 align-middle" style="background-color: {tech.color}; opacity: 0.7;"></span>
						{tech.name}
					</div>
				{/each}
			</div>
		</div>
	</section>

	<!-- ═══════════════════════════════════════ FOOTER ═════════════════════════════════════ -->
	<footer class="py-16 relative">
		<div class="pointer-events-none absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-[#F2EEE8]/[0.06] to-transparent"></div>

		<div class="max-w-5xl mx-auto px-6 sm:px-10 text-center">
			<p class="font-display text-2xl italic text-[#F2EEE8]/20 mb-6">Lectorius</p>
			<p class="text-sm text-[#F2EEE8]/30 font-sans mb-5">
				Built by Jan Barganowski
			</p>
			<div class="flex items-center justify-center gap-6">
				<a
					href="https://github.com/jan-barg/lectorius"
					target="_blank"
					rel="noopener noreferrer"
					class="text-[#F2EEE8]/25 hover:text-[#F2EEE8]/60 transition-colors duration-300"
					aria-label="GitHub"
				>
					<svg class="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
						<path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
					</svg>
				</a>
				<a
					href="https://www.linkedin.com/in/janbarg/"
					target="_blank"
					rel="noopener noreferrer"
					class="text-[#F2EEE8]/25 hover:text-[#F2EEE8]/60 transition-colors duration-300"
					aria-label="LinkedIn"
				>
					<svg class="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
						<path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
					</svg>
				</a>
			</div>
		</div>
	</footer>

</div>
</div>

<style>
	/* ─── Hero title ─── */
	.hero-title {
		font-size: clamp(4.5rem, 19vw, 16rem);
		color: #F2EEE8;
		text-shadow: 0 0 120px rgba(220, 160, 114, 0.12);
	}

	/* ─── Demo button states ─── */
	.demo-btn {
		border: 1px solid transparent;
		transition: background 0.7s ease, color 0.7s ease, border-color 0.7s ease, box-shadow 0.7s ease;
	}
	.demo-btn-idle {
		background: #161310;
		border-color: rgba(242, 238, 232, 0.08);
		color: #F2EEE8;
	}
	.demo-btn-listening {
		background: #DCA072;
		color: #0A0908;
		box-shadow: 0 20px 25px -5px rgba(220, 160, 114, 0.2);
	}
	.demo-btn-thinking {
		background: #161310;
		border-color: rgba(220, 160, 114, 0.3);
		color: #DCA072;
	}
	.demo-btn-speaking {
		background: rgba(220, 160, 114, 0.9);
		color: #fff;
		box-shadow: 0 20px 25px -5px rgba(220, 160, 114, 0.2);
	}

	/* ─── Fake cursor ─── */
	.demo-cursor {
		opacity: 0;
		transform: translate(60px, 50px);
		transition: opacity 0.7s ease, transform 0.8s cubic-bezier(0.22, 1, 0.36, 1);
		filter: drop-shadow(0 2px 6px rgba(0,0,0,0.4));
	}
	.demo-cursor.cursor-visible {
		opacity: 1;
		transform: translate(0, 0);
	}
	.demo-cursor.cursor-pressed {
		transform: translate(-2px, 2px) scale(0.9);
	}

	/* ─── Recording dot blink ─── */
	@keyframes rec-blink {
		0%, 100% { opacity: 0.6; }
		50% { opacity: 1; }
	}
	.recording-dot {
		animation: rec-blink 1s ease-in-out infinite;
	}

	/* ─── Mini wave bars (speaking state) ─── */
	@keyframes mini-wave {
		0%, 100% { height: 4px; }
		50% { height: 16px; }
	}
	.wave-bar-mini {
		display: inline-block;
		width: 2px;
		height: 4px;
		background: currentColor;
		border-radius: 9999px;
		animation: mini-wave ease-in-out infinite;
	}

	/* ─── Scroll indicator pulse ─── */
	@keyframes scroll-pulse {
		0%, 100% { opacity: 0.4; transform: scaleY(1); }
		50% { opacity: 0.8; transform: scaleY(1.2); }
	}
	.scroll-line {
		animation: scroll-pulse 2s ease-in-out infinite;
		transform-origin: top;
	}

	/* ─── Landing page base ─── */
	.landing-page {
		font-feature-settings: 'kern' 1, 'liga' 1;
	}
</style>
