<script lang="ts">
	import type { BookListItem } from '$lib/types';
	import BookCardVideo from './BookCardVideo.svelte';
	import ProgressOverlay from './ProgressOverlay.svelte';

	export let book: BookListItem;
	export let progress: number | null = null;

	let hovering = false;

	$: isComingSoon = book.status === 'coming_soon';

	function formatDuration(ms: number): string {
		const hours = Math.floor(ms / 3600000);
		const minutes = Math.floor((ms % 3600000) / 60000);
		if (hours > 0) return `${hours}h ${minutes}m`;
		return `${minutes}m`;
	}
</script>

{#snippet cardContent()}
	<div class="relative w-full aspect-[3/4] overflow-hidden bg-stone-200 dark:bg-slate-800 {isComingSoon ? 'grayscale-[30%] opacity-80' : ''}">
		<BookCardVideo
			src={book.cover_video_url}
			{hovering}
			fallbackChar={book.title.charAt(0)}
		/>

		<!-- Coming Soon badge -->
		{#if isComingSoon}
			<div class="absolute top-3 right-3 z-20">
				<span class="px-2.5 py-1 rounded-full text-[10px] font-bold tracking-wider uppercase bg-accent text-white shadow-lg shadow-accent/20">
					Coming Soon
				</span>
			</div>
		{/if}

		<!-- Glassmorphism blur layer (masked to fade in smoothly) -->
		<div
			class="pointer-events-none absolute bottom-0 inset-x-0 z-[9] h-2/3 backdrop-blur-md"
			style="-webkit-mask-image: linear-gradient(to bottom, transparent 0%, black 100%); mask-image: linear-gradient(to bottom, transparent 0%, black 100%);"
		></div>

		<!-- Gradient overlay with metadata -->
		<div class="pointer-events-none absolute bottom-0 inset-x-0 z-10 flex flex-col justify-end p-4 pt-12 bg-gradient-to-t from-black/60 via-black/25 to-transparent">
			<h3 class="text-lg font-bold leading-tight text-white drop-shadow-md line-clamp-2 group-hover:text-violet-100 transition-colors">
				{book.title}
			</h3>
			{#if book.author}
				<p class="mt-1 text-xs font-medium text-stone-300 group-hover:text-white transition-colors">
					{book.author}
				</p>
			{/if}
		</div>

		<!-- Progress bar -->
		{#if progress !== null && !isComingSoon}
			<div class="absolute bottom-0 left-0 w-full z-20">
				<ProgressOverlay percentage={progress} />
			</div>
		{/if}
	</div>

	<!-- Info below cover -->
	<div class="px-3 py-2">
		<div class="flex items-center gap-2 text-xs text-muted">
			<span>{book.total_chapters} chapters</span>
			<span class="text-muted/50">|</span>
			<span>{formatDuration(book.total_duration_ms)}</span>
		</div>
	</div>
{/snippet}

{#if isComingSoon}
	<div
		class="group block overflow-hidden rounded-xl bg-surface cursor-not-allowed"
		on:mouseenter={() => (hovering = true)}
		on:mouseleave={() => (hovering = false)}
		role="img"
		aria-label="{book.title} — coming soon"
	>
		{@render cardContent()}
	</div>
{:else}
	<a
		href="/book/{book.book_id}"
		class="group block overflow-hidden rounded-xl bg-surface transition-all duration-200 hover:-translate-y-2 hover:ring-2 hover:ring-accent/50"
		on:mouseenter={() => (hovering = true)}
		on:mouseleave={() => (hovering = false)}
	>
		{@render cardContent()}
	</a>
{/if}
