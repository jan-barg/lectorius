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

	/* ─── Mouse-following spotlight ─── */
	let heroEl: HTMLElement;
	let spotX = 50;
	let spotY = 50;
	let targetX = 50;
	let targetY = 50;
	let spotActive = false;
	let rafId: number;

	/* ─── Parallax glow orbs ─── */
	let scrollY = 0;
	let pageEl: HTMLElement;

	/* ─── Typewriter reveal ─── */
	const line1 = 'Books that';
	const line2 = 'talk back.';
	let typed1 = '';
	let typed2 = '';
	let typingDone = false;

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

		// ─── Typewriter reveal ───
		const totalChars = line1.length + line2.length;
		let charIndex = 0;
		const typeSpeed = 70; // ms per character
		const typeDelay = 600; // initial delay before typing starts

		setTimeout(() => {
			const typeInterval = setInterval(() => {
				if (charIndex < line1.length) {
					typed1 = line1.slice(0, charIndex + 1);
				} else {
					typed2 = line2.slice(0, charIndex - line1.length + 1);
				}
				charIndex++;
				if (charIndex >= totalChars) {
					clearInterval(typeInterval);
					typingDone = true;
				}
			}, typeSpeed);
		}, typeDelay);

		// ─── Parallax glow orbs ───
		function onScroll() {
			scrollY = window.scrollY;
			if (pageEl) {
				pageEl.style.setProperty('--scroll', `${scrollY}`);
			}
		}
		window.addEventListener('scroll', onScroll, { passive: true });
		onScroll();

		// ─── Mouse-following spotlight ───
		function onHeroMove(e: MouseEvent) {
			if (!heroEl) return;
			const rect = heroEl.getBoundingClientRect();
			targetX = ((e.clientX - rect.left) / rect.width) * 100;
			targetY = ((e.clientY - rect.top) / rect.height) * 100;
			if (!spotActive) spotActive = true;
		}
		function onHeroLeave() {
			spotActive = false;
		}

		function lerpSpot() {
			spotX += (targetX - spotX) * 0.08;
			spotY += (targetY - spotY) * 0.08;
			if (heroEl) {
				heroEl.style.setProperty('--spot-x', `${spotX}%`);
				heroEl.style.setProperty('--spot-y', `${spotY}%`);
			}
			rafId = requestAnimationFrame(lerpSpot);
		}

		if (heroEl) {
			heroEl.addEventListener('mousemove', onHeroMove);
			heroEl.addEventListener('mouseleave', onHeroLeave);
			rafId = requestAnimationFrame(lerpSpot);
		}

		return () => {
			observer.disconnect();
			window.removeEventListener('scroll', onScroll);
			if (heroEl) {
				heroEl.removeEventListener('mousemove', onHeroMove);
				heroEl.removeEventListener('mouseleave', onHeroLeave);
			}
			cancelAnimationFrame(rafId);
		};
	});

	const techStack = [
		{ name: 'ElevenLabs', color: '#FFFFFF', logo: '<path d="M4.6035 0v24h4.9317V0zm9.8613 0v24h4.9317V0z"/>' },
		{ name: 'Claude', color: '#D4A27F', logo: '<path d="M17.3041 3.541h-3.6718l6.696 16.918H24Zm-10.6082 0L0 20.459h3.7442l1.3693-3.5527h7.0052l1.3693 3.5528h3.7442L10.5363 3.5409Zm-.3712 10.2232 2.2914-5.9456 2.2914 5.9456Z"/>' },
		{ name: 'OpenAI', color: '#FFFFFF', logo: '<path d="M22.2819 9.8211a5.9847 5.9847 0 0 0-.5157-4.9108 6.0462 6.0462 0 0 0-6.5098-2.9A6.0651 6.0651 0 0 0 4.9807 4.1818a5.9847 5.9847 0 0 0-3.9977 2.9 6.0462 6.0462 0 0 0 .7427 7.0966 5.98 5.98 0 0 0 .511 4.9107 6.051 6.051 0 0 0 6.5146 2.9001A5.9847 5.9847 0 0 0 13.2599 24a6.0557 6.0557 0 0 0 5.7718-4.2058 5.9894 5.9894 0 0 0 3.9977-2.9001 6.0557 6.0557 0 0 0-.7475-7.0729zm-9.022 12.6081a4.4755 4.4755 0 0 1-2.8764-1.0408l.1419-.0804 4.7783-2.7582a.7948.7948 0 0 0 .3927-.6813v-6.7369l2.02 1.1686a.071.071 0 0 1 .038.052v5.5826a4.504 4.504 0 0 1-4.4945 4.4944zm-9.6607-4.1254a4.4708 4.4708 0 0 1-.5346-3.0137l.142.0852 4.783 2.7582a.7712.7712 0 0 0 .7806 0l5.8428-3.3685v2.3324a.0804.0804 0 0 1-.0332.0615L9.74 19.9502a4.4992 4.4992 0 0 1-6.1408-1.6464zM2.3408 7.8956a4.485 4.485 0 0 1 2.3655-1.9728V11.6a.7664.7664 0 0 0 .3879.6765l5.8144 3.3543-2.0201 1.1685a.0757.0757 0 0 1-.071 0l-4.8303-2.7865A4.504 4.504 0 0 1 2.3408 7.872zm16.5963 3.8558L13.1038 8.364 15.1192 7.2a.0757.0757 0 0 1 .071 0l4.8303 2.7913a4.4944 4.4944 0 0 1-.6765 8.1042v-5.6772a.79.79 0 0 0-.407-.667zm2.0107-3.0231l-.142-.0852-4.7735-2.7818a.7759.7759 0 0 0-.7854 0L9.409 9.2297V6.8974a.0662.0662 0 0 1 .0284-.0615l4.8303-2.7866a4.4992 4.4992 0 0 1 6.6802 4.66zM8.3065 12.863l-2.02-1.1638a.0804.0804 0 0 1-.038-.0567V6.0742a4.4992 4.4992 0 0 1 7.3757-3.4537l-.142.0805L8.704 5.459a.7948.7948 0 0 0-.3927.6813zm1.0976-2.3654l2.602-1.4998 2.6069 1.4998v2.9994l-2.5974 1.4997-2.6067-1.4997Z"/>' },
		{ name: 'SvelteKit', color: '#FF3E00', logo: '<path d="M10.354 21.125a4.44 4.44 0 0 1-4.765-1.767 4.109 4.109 0 0 1-.703-3.107 3.898 3.898 0 0 1 .134-.522l.105-.321.287.21a7.21 7.21 0 0 0 2.186 1.092l.208.063-.02.208a1.253 1.253 0 0 0 .226.83 1.337 1.337 0 0 0 1.435.533 1.231 1.231 0 0 0 .343-.15l5.59-3.562a1.164 1.164 0 0 0 .524-.778 1.242 1.242 0 0 0-.211-.937 1.338 1.338 0 0 0-1.435-.533 1.23 1.23 0 0 0-.343.15l-2.133 1.36a4.078 4.078 0 0 1-1.135.499 4.44 4.44 0 0 1-4.765-1.766 4.108 4.108 0 0 1-.702-3.108 3.855 3.855 0 0 1 1.742-2.582l5.589-3.563a4.072 4.072 0 0 1 1.135-.499 4.44 4.44 0 0 1 4.765 1.767 4.109 4.109 0 0 1 .703 3.107 3.943 3.943 0 0 1-.134.522l-.105.321-.286-.21a7.204 7.204 0 0 0-2.187-1.093l-.208-.063.02-.207a1.255 1.255 0 0 0-.226-.831 1.337 1.337 0 0 0-1.435-.532 1.231 1.231 0 0 0-.343.15L8.62 9.368a1.162 1.162 0 0 0-.524.778 1.24 1.24 0 0 0 .211.937 1.338 1.338 0 0 0 1.435.533 1.235 1.235 0 0 0 .344-.151l2.132-1.36a4.067 4.067 0 0 1 1.135-.498 4.44 4.44 0 0 1 4.765 1.766 4.108 4.108 0 0 1 .702 3.108 3.857 3.857 0 0 1-1.742 2.583l-5.589 3.562a4.072 4.072 0 0 1-1.135.499m10.358-17.95C18.484-.015 14.082-.96 10.9 1.068L5.31 4.63a6.412 6.412 0 0 0-2.896 4.295 6.753 6.753 0 0 0 .666 4.336 6.43 6.43 0 0 0-.96 2.396 6.833 6.833 0 0 0 1.168 5.167c2.229 3.19 6.63 4.135 9.812 2.108l5.59-3.562a6.41 6.41 0 0 0 2.896-4.295 6.756 6.756 0 0 0-.665-4.336 6.429 6.429 0 0 0 .958-2.396 6.831 6.831 0 0 0-1.167-5.168Z"/>' },
		{ name: 'TypeScript', color: '#3178C6', logo: '<path d="M1.125 0C.502 0 0 .502 0 1.125v21.75C0 23.498.502 24 1.125 24h21.75c.623 0 1.125-.502 1.125-1.125V1.125C24 .502 23.498 0 22.875 0zm17.363 9.75c.612 0 1.154.037 1.627.111a6.38 6.38 0 0 1 1.306.34v2.458a3.95 3.95 0 0 0-.643-.361 5.093 5.093 0 0 0-.717-.26 5.453 5.453 0 0 0-1.426-.2c-.3 0-.573.028-.819.086a2.1 2.1 0 0 0-.623.242c-.17.104-.3.229-.393.374a.888.888 0 0 0-.14.49c0 .196.053.373.156.529.104.156.252.304.443.444s.423.276.696.41c.273.135.582.274.926.416.47.197.892.407 1.266.628.374.222.695.473.963.753.268.279.472.598.614.957.142.359.214.776.214 1.253 0 .657-.125 1.21-.373 1.656a3.033 3.033 0 0 1-1.012 1.085 4.38 4.38 0 0 1-1.487.596c-.566.12-1.163.18-1.79.18a9.916 9.916 0 0 1-1.84-.164 5.544 5.544 0 0 1-1.512-.493v-2.63a5.033 5.033 0 0 0 3.237 1.2c.333 0 .624-.03.872-.09.249-.06.456-.144.623-.25.166-.108.29-.234.373-.38a1.023 1.023 0 0 0-.074-1.089 2.12 2.12 0 0 0-.537-.5 5.597 5.597 0 0 0-.807-.444 27.72 27.72 0 0 0-1.007-.436c-.918-.383-1.602-.852-2.053-1.405-.45-.553-.676-1.222-.676-2.005 0-.614.123-1.141.369-1.582.246-.441.58-.804 1.004-1.089a4.494 4.494 0 0 1 1.47-.629 7.536 7.536 0 0 1 1.77-.201zm-15.113.188h9.563v2.166H9.506v9.646H6.789v-9.646H3.375z"/>' },
		{ name: 'Tailwind', color: '#38BDF8', logo: '<path d="M12.001,4.8c-3.2,0-5.2,1.6-6,4.8c1.2-1.6,2.6-2.2,4.2-1.8c0.913,0.228,1.565,0.89,2.288,1.624C13.666,10.618,15.027,12,18.001,12c3.2,0,5.2-1.6,6-4.8c-1.2,1.6-2.6,2.2-4.2,1.8c-0.913-0.228-1.565-0.89-2.288-1.624C16.337,6.182,14.976,4.8,12.001,4.8z M6.001,12c-3.2,0-5.2,1.6-6,4.8c1.2-1.6,2.6-2.2,4.2-1.8c0.913,0.228,1.565,0.89,2.288,1.624c1.177,1.194,2.538,2.576,5.512,2.576c3.2,0,5.2-1.6,6-4.8c-1.2,1.6-2.6,2.2-4.2,1.8c-0.913-0.228-1.565-0.89-2.288-1.624C10.337,13.382,8.976,12,6.001,12z"/>' },
		{ name: 'Python', color: '#F7D44F', logo: '<path d="M14.25.18l.9.2.73.26.59.3.45.32.34.34.25.34.16.33.1.3.04.26.02.2-.01.13V8.5l-.05.63-.13.55-.21.46-.26.38-.3.31-.33.25-.35.19-.35.14-.33.1-.3.07-.26.04-.21.02H8.77l-.69.05-.59.14-.5.22-.41.27-.33.32-.27.35-.2.36-.15.37-.1.35-.07.32-.04.27-.02.21v3.06H3.17l-.21-.03-.28-.07-.32-.12-.35-.18-.36-.26-.36-.36-.35-.46-.32-.59-.28-.73-.21-.88-.14-1.05-.05-1.23.06-1.22.16-1.04.24-.87.32-.71.36-.57.4-.44.42-.33.42-.24.4-.16.36-.1.32-.05.24-.01h.16l.06.01h8.16v-.83H6.18l-.01-2.75-.02-.37.05-.34.11-.31.17-.28.25-.26.31-.23.38-.2.44-.18.51-.15.58-.12.64-.1.71-.06.77-.04.84-.02 1.27.05zm-6.3 1.98l-.23.33-.08.41.08.41.23.34.33.22.41.09.41-.09.33-.22.23-.34.08-.41-.08-.41-.23-.33-.33-.22-.41-.09-.41.09zm13.09 3.95l.28.06.32.12.35.18.36.27.36.35.35.47.32.59.28.73.21.88.14 1.04.05 1.23-.06 1.23-.16 1.04-.24.86-.32.71-.36.57-.4.45-.42.33-.42.24-.4.16-.36.09-.32.05-.24.02-.16-.01h-8.22v.82h5.84l.01 2.76.02.36-.05.34-.11.31-.17.29-.25.25-.31.24-.38.2-.44.17-.51.15-.58.13-.64.09-.71.07-.77.04-.84.01-1.27-.04-1.07-.14-.9-.2-.73-.25-.59-.3-.45-.33-.34-.34-.25-.34-.16-.33-.1-.3-.04-.25-.02-.2.01-.13v-5.34l.05-.64.13-.54.21-.46.26-.38.3-.32.33-.24.35-.2.35-.14.33-.1.3-.06.26-.04.21-.02.13-.01h5.84l.69-.05.59-.14.5-.21.41-.28.33-.32.27-.35.2-.36.15-.36.1-.35.07-.32.04-.28.02-.21V6.07h2.09l.14.01zm-6.47 14.25l-.23.33-.08.41.08.41.23.33.33.23.41.08.41-.08.33-.23.23-.33.08-.41-.08-.41-.23-.33-.33-.23-.41-.08-.41.08z"/>' },
		{ name: 'pgvector', color: '#336791', logo: '<path d="M23.5594 14.7228a.5269.5269 0 0 0-.0563-.1191c-.139-.2632-.4768-.3418-1.0074-.2321-1.6533.3411-2.2935.1312-2.5256-.0191 1.342-2.0482 2.445-4.522 3.0411-6.8297.2714-1.0507.7982-3.5237.1222-4.7316a1.5641 1.5641 0 0 0-.1509-.235C21.6931.9086 19.8007.0248 17.5099.0005c-1.4947-.0158-2.7705.3461-3.1161.4794a9.449 9.449 0 0 0-.5159-.0816 8.044 8.044 0 0 0-1.3114-.1278c-1.1822-.0184-2.2038.2642-3.0498.8406-.8573-.3211-4.7888-1.645-7.2219.0788C.9359 2.1526.3086 3.8733.4302 6.3043c.0409.818.5069 3.334 1.2423 5.7436.4598 1.5065.9387 2.7019 1.4334 3.582.553.9942 1.1259 1.5933 1.7143 1.7895.4474.1491 1.1327.1441 1.8581-.7279.8012-.9635 1.5903-1.8258 1.9446-2.2069.4351.2355.9064.3625 1.39.3772a.0569.0569 0 0 0 .0004.0041 11.0312 11.0312 0 0 0-.2472.3054c-.3389.4302-.4094.5197-1.5002.7443-.3102.064-1.1344.2339-1.1464.8115-.0025.1224.0329.2309.0919.3268.2269.4231.9216.6097 1.015.6331 1.3345.3335 2.5044.092 3.3714-.6787-.017 2.231.0775 4.4174.3454 5.0874.2212.5529.7618 1.9045 2.4692 1.9043.2505 0 .5263-.0291.8296-.0941 1.7819-.3821 2.5557-1.1696 2.855-2.9059.1503-.8707.4016-2.8753.5388-4.1012.0169-.0703.0357-.1207.057-.1362.0007-.0005.0697-.0471.4272.0307a.3673.3673 0 0 0 .0443.0068l.2539.0223.0149.001c.8468.0384 1.9114-.1426 2.5312-.4308.6438-.2988 1.8057-1.0323 1.5951-1.6698z"/>' },
		{ name: 'Supabase', color: '#3ECF8E', logo: '<path d="M11.9 1.036c-.015-.986-1.26-1.41-1.874-.637L.764 12.05C-.33 13.427.65 15.455 2.409 15.455h9.579l.113 7.51c.014.985 1.259 1.408 1.873.636l9.262-11.653c1.093-1.375.113-3.403-1.645-3.403h-9.642z"/>' },
		{ name: 'Upstash', color: '#00E9A3', logo: '<path d="M13.8027 0C11.193 0 8.583.9952 6.5918 2.9863c-3.9823 3.9823-3.9823 10.4396 0 14.4219 1.9911 1.9911 5.2198 1.9911 7.211 0 1.991-1.9911 1.991-5.2198 0-7.211L12 12c.9956.9956.9956 2.6098 0 3.6055-.9956.9955-2.6099.9955-3.6055 0-2.9866-2.9868-2.9866-7.8297 0-10.8164 2.9868-2.9868 7.8297-2.9868 10.8164 0l1.8028-1.8028C19.0225.9952 16.4125 0 13.8027 0zM12 12c-.9956-.9956-.9956-2.6098 0-3.6055.9956-.9955 2.6098-.9955 3.6055 0 2.9867 2.9868 2.9867 7.8297 0 10.8164-2.9867 2.9868-7.8297 2.9868-10.8164 0l-1.8028 1.8028c3.9823 3.9822 10.4396 3.9822 14.4219 0 3.9823-3.9824 3.9823-10.4396 0-14.4219-.9956-.9956-2.3006-1.4922-3.6055-1.4922-1.3048 0-2.6099.4966-3.6054 1.4922-1.9912 1.9912-1.9912 5.2198 0 7.211z"/>' },
	];
</script>

<svelte:head>
	<title>Lectorius — Books that talk back</title>
	<meta name="description" content="Listen to books narrated by AI voices matched to each story's era and tone. Ask questions, get spoiler-free answers. Literature, reimagined." />
</svelte:head>

<div class="dark">
<div bind:this={pageEl} class="landing-page grain-overlay relative min-h-screen bg-[#0A0908] text-[#F2EEE8] overflow-x-hidden">

	<!-- Parallax glow orbs — drift at different rates as you scroll -->
	<div class="parallax-orb orb-1" aria-hidden="true"></div>
	<div class="parallax-orb orb-2" aria-hidden="true"></div>
	<div class="parallax-orb orb-3" aria-hidden="true"></div>

	<!-- ═══════════════════════════════════════ HERO ═══════════════════════════════════════ -->
	<section bind:this={heroEl} class="relative min-h-screen flex flex-col overflow-hidden">
		<!-- Mouse-following candlelight spotlight -->
		<div
			class="hero-spotlight pointer-events-none absolute inset-0 z-[1] will-change-transform"
			class:spotlight-active={spotActive}
		></div>

		<!-- Ambient glows -->
		<div class="pointer-events-none absolute top-[-200px] left-[-100px] h-[600px] w-[600px] rounded-full bg-[#DCA072]/[0.06] blur-[180px] will-change-transform"></div>
		<div class="pointer-events-none absolute bottom-[-100px] right-[-150px] h-[500px] w-[500px] rounded-full bg-[#BC6A34]/[0.04] blur-[160px] will-change-transform"></div>

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
						<span class="block text-6xl sm:text-7xl md:text-8xl lg:text-[6.5rem] xl:text-[7.5rem] font-light text-[#F2EEE8]">{typed1}{#if !typingDone && typed1.length < line1.length}<span class="type-cursor"></span>{/if}<span class="invisible" aria-hidden="true">{line1.slice(typed1.length)}</span></span>
						<span class="block text-6xl sm:text-7xl md:text-8xl lg:text-[6.5rem] xl:text-[7.5rem] font-light italic text-[#DCA072]">{typed2}{#if !typingDone && typed2.length > 0}<span class="type-cursor"></span>{/if}<span class="invisible" aria-hidden="true">{line2.slice(typed2.length)}</span></span>
					</h2>
					<p class="mt-8 md:mt-10 text-[#F2EEE8]/50 font-sans text-lg sm:text-xl md:text-2xl leading-relaxed max-w-xl mx-auto lg:mx-0 animate-fade-in-up stagger-3">
						Listen to classic literature narrated by AI voices matched to each story's era and tone. Then ask anything — spoiler-free.
					</p>
					<div class="mt-12 md:mt-14 animate-fade-in-up stagger-4">
						<a
							href="/library"
							class="group inline-flex items-center gap-5 rounded-2xl bg-[#DCA072] px-14 py-6 text-lg md:text-xl font-bold text-[#0A0908] shadow-xl shadow-[#DCA072]/20 transition-[transform,box-shadow] duration-300 hover:bg-[#E4AD82] hover:shadow-2xl hover:shadow-[#DCA072]/30 hover:translate-y-[-2px]"
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
							class="demo-bubble absolute left-0 right-12 sm:right-20"
							class:revealed={showQuestion}
							style="top: 12%; --hide-x: -30px;"
						>
							<div class="rounded-2xl rounded-bl-sm border border-[#F2EEE8]/[0.07] bg-[#161310] px-6 py-4 shadow-lg shadow-black/20">
								<p class="font-sans text-base sm:text-lg text-[#F2EEE8]/80 leading-relaxed">{currentQA.q}</p>
							</div>
						</div>

						<!-- The Button -->
						<div class="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2">
							<!-- Idle glow rings (always in DOM, toggled via opacity) -->
							<div class="absolute inset-0 -m-4 rounded-full bg-[#DCA072]/10 animate-soft-ping transition-opacity duration-300" class:opacity-0={phase !== 'reading' && phase !== 'cursor-in'}></div>
							<div class="absolute inset-0 -m-2 rounded-full bg-[#DCA072]/5 animate-glow-pulse transition-opacity duration-300" class:opacity-0={phase !== 'reading' && phase !== 'cursor-in'}></div>

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
							class="demo-bubble absolute left-12 sm:left-20 right-0"
							class:revealed={showAnswer}
							style="bottom: 8%; --hide-x: 30px;"
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
			<div class="reveal-header text-center mb-20" class:revealed={visible['how-it-works']}>
				<p class="text-[#DCA072] font-sans text-xs tracking-[0.35em] uppercase font-semibold mb-4">How it works</p>
				<h2 class="font-display text-4xl md:text-5xl font-light tracking-[-0.02em]">Three steps to a living book</h2>
			</div>

			<div class="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-10">
				{#each [
					{
						step: '01',
						title: 'Pick a book',
						desc: 'Browse a library of books, each with its own voice and atmosphere.',
						icon: 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253'
					},
					{
						step: '02',
						title: 'Listen',
						desc: 'AI narration matched to the book\'s era and tone, with ambient music to set the scene.',
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
						class="group reveal-card relative rounded-2xl border border-[#F2EEE8]/[0.05] bg-[#161310]/60 p-8 md:p-10 transition-[border-color,background-color] duration-700 hover:border-[#DCA072]/20 hover:bg-[#161310]"
						class:revealed={visible['how-it-works']}
						style="transition-delay: {i * 150}ms;"
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
			<div class="reveal-header text-center mb-20" class:revealed={visible['features']}>
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
						class="group reveal-card relative rounded-2xl border border-[#F2EEE8]/[0.05] bg-[#161310]/40 p-8 transition-[border-color,background-color] duration-700 hover:border-[#DCA072]/15 hover:bg-[#161310]/70"
						class:revealed={visible['features']}
						style="transition-delay: {i * 120}ms;"
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
			<div class="reveal-header text-center mb-16" class:revealed={visible['tech-stack']}>
				<p class="text-[#DCA072] font-sans text-xs tracking-[0.35em] uppercase font-semibold">Built with</p>
			</div>

			<div class="flex flex-wrap justify-center gap-3 md:gap-4">
				{#each techStack as tech, i}
					<div
						class="reveal-card flex items-center gap-2.5 rounded-xl border border-[#F2EEE8]/[0.06] bg-[#161310]/60 px-5 py-3 font-sans text-sm font-medium text-[#F2EEE8]/70 transition-[border-color,color] duration-500 hover:border-[#DCA072]/20 hover:text-[#F2EEE8]/90"
						class:revealed={visible['tech-stack']}
						style="transition-delay: {i * 70}ms;"
					>
						<svg class="h-4 w-4 flex-shrink-0" viewBox="0 0 24 24" fill={tech.color} style="opacity: 0.8;">
							{@html tech.logo}
						</svg>
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

	/* ─── Scroll-reveal cards ─── */
	.reveal-card {
		opacity: 0;
		transform: translateY(30px);
		transition-property: opacity, transform, border-color, background-color, color;
		transition-timing-function: ease;
	}
	.reveal-card.revealed {
		opacity: 1;
		transform: translateY(0);
	}

	/* ─── Scroll-reveal section headers ─── */
	.reveal-header {
		opacity: 0;
		transform: translateY(8px);
		transition: opacity 1s ease, transform 1s ease;
	}
	.reveal-header.revealed {
		opacity: 1;
		transform: translateY(0);
	}

	/* ─── Demo bubbles (question / answer) ─── */
	.demo-bubble {
		opacity: 0;
		transform: translateX(var(--hide-x, 0));
		transition: opacity 0.7s ease-in-out, transform 0.7s ease-in-out;
	}
	.demo-bubble.revealed {
		opacity: 1;
		transform: translateX(0);
	}

	/* ─── Typewriter cursor ─── */
	@keyframes cursor-blink {
		0%, 100% { opacity: 1; }
		50% { opacity: 0; }
	}
	.type-cursor {
		display: inline-block;
		width: 3px;
		height: 0.7em;
		background: #DCA072;
		margin-left: 4px;
		vertical-align: middle;
		animation: cursor-blink 0.8s step-end infinite;
	}

	/* ─── Parallax glow orbs ─── */
	.parallax-orb {
		position: fixed;
		border-radius: 50%;
		pointer-events: none;
		filter: blur(120px);
		will-change: transform;
		z-index: 0;
	}
	.orb-1 {
		width: 500px;
		height: 500px;
		background: rgba(220, 160, 114, 0.04);
		left: -10%;
		top: 30%;
		transform: translateY(calc(var(--scroll, 0) * -0.15px));
	}
	.orb-2 {
		width: 350px;
		height: 350px;
		background: rgba(188, 106, 52, 0.035);
		right: -5%;
		top: 55%;
		transform: translateY(calc(var(--scroll, 0) * -0.25px));
	}
	.orb-3 {
		width: 420px;
		height: 420px;
		background: rgba(212, 162, 127, 0.025);
		left: 40%;
		top: 80%;
		transform: translateY(calc(var(--scroll, 0) * -0.35px));
	}

	/* ─── Mouse-following candlelight spotlight ─── */
	.hero-spotlight {
		background: radial-gradient(
			ellipse 600px 500px at var(--spot-x, 50%) var(--spot-y, 50%),
			rgba(220, 160, 114, 0.06) 0%,
			rgba(220, 160, 114, 0.02) 40%,
			transparent 70%
		);
		opacity: 0;
		transition: opacity 0.8s ease;
	}
	.hero-spotlight.spotlight-active {
		opacity: 1;
	}

	/* ─── Landing page base ─── */
	.landing-page {
		font-feature-settings: 'kern' 1, 'liga' 1;
	}
</style>
