<script lang="ts">
	import { fly, fade } from 'svelte/transition';
	import ThemeSwitcher from './ThemeSwitcher.svelte';
	import { clearAllReadingHistory } from '$lib/stores/reading-history';
	import { userName } from '$lib/stores/user';

	export let open = false;
	export let onClose: () => void;

	/** 'idle' | 'confirm' | 'feedback' */
	let state = 'idle';

	let nameInput = '';
	let codeInput = '';
	let codeError = '';
	let codeLoading = false;
	let codeSuccess = false;

	$: if (open) nameInput = $userName;

	function handleNameBlur() {
		const trimmed = nameInput.trim();
		userName.setName(trimmed);
		nameInput = trimmed;
	}

	async function handleVerifyCode() {
		if (!codeInput.trim()) return;
		codeLoading = true;
		codeError = '';
		try {
			const res = await fetch('/api/verify-code', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ code: codeInput.trim() })
			});
			if (res.ok) {
				codeInput = '';
				codeSuccess = true;
			} else {
				codeError = 'Invalid code, try again';
			}
		} catch {
			codeError = 'Something went wrong';
		} finally {
			codeLoading = false;
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape') {
			if (state === 'confirm') {
				state = 'idle';
			} else {
				onClose();
			}
		}
	}

	function handleDelete() {
		clearAllReadingHistory();
		state = 'feedback';
		setTimeout(() => {
			state = 'idle';
		}, 2000);
	}
</script>

<svelte:window onkeydown={handleKeydown} />

{#if open}
	<!-- Backdrop -->
	<button
		class="fixed inset-0 z-40 bg-black/30 dark:bg-black/50"
		onclick={onClose}
		aria-label="Close settings"
		transition:fade={{ duration: 200 }}
	></button>

	<!-- Panel -->
	<div
		class="fixed top-0 right-0 z-50 h-full w-80 bg-background border-l border-text/[0.06] dark:border-white/[0.06] p-7 shadow-2xl shadow-black/10 dark:shadow-black/30"
		transition:fly={{ x: 320, duration: 300, opacity: 1 }}
	>
		<div class="mb-8 flex items-center justify-between">
			<h2 class="font-display text-lg text-text">Settings</h2>
			<button class="rounded-full p-1.5 text-muted hover:text-text transition-colors" onclick={onClose} aria-label="Close">
				<svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
				</svg>
			</button>
		</div>

		<div class="space-y-7">
			<div>
				<span class="mb-2 block text-[11px] font-semibold uppercase tracking-[0.12em] text-muted/60">Name</span>
				<input
					type="text"
					bind:value={nameInput}
					onblur={handleNameBlur}
					onkeydown={(e) => e.key === 'Enter' && e.currentTarget.blur()}
					class="w-full rounded-lg border border-text/[0.08] dark:border-white/[0.08] bg-surface px-3 py-2.5 text-sm text-text placeholder:text-muted/40 outline-none focus:border-accent/40 focus:ring-2 focus:ring-accent/10 transition-all"
					placeholder="Enter your name"
				/>
			</div>

			<div>
				<span class="mb-2 block text-[11px] font-semibold uppercase tracking-[0.12em] text-muted/60">Theme</span>
				<ThemeSwitcher />
			</div>

			<div>
				<span class="mb-2 block text-[11px] font-semibold uppercase tracking-[0.12em] text-muted/60">Unlimited Questions Access</span>
				{#if codeSuccess}
					<p class="text-sm text-green-600 dark:text-green-400 font-medium">Unlimited access &#10003;</p>
				{:else}
					<div class="space-y-2">
						<input
							type="text"
							bind:value={codeInput}
							onkeydown={(e) => e.key === 'Enter' && handleVerifyCode()}
							placeholder="Enter access code"
							class="w-full rounded-lg border border-text/[0.08] dark:border-white/[0.08] bg-surface px-3 py-2.5 text-sm text-text placeholder:text-muted/40 outline-none focus:border-accent/40 focus:ring-2 focus:ring-accent/10 transition-all"
						/>
						<button
							onclick={handleVerifyCode}
							disabled={!codeInput.trim() || codeLoading}
							class="w-full rounded-lg bg-accent px-4 py-2.5 text-sm font-semibold text-white transition-all hover:brightness-110 disabled:opacity-30"
						>
							{codeLoading ? 'Verifying...' : 'Unlock'}
						</button>
						{#if codeError}
							<p class="text-xs text-red-400/80">{codeError}</p>
						{/if}
					</div>
				{/if}
			</div>
		</div>

		<!-- Danger zone -->
		<div class="mt-12 border-t border-text/[0.06] dark:border-white/[0.06] pt-6">
			<span class="mb-3 block text-[10px] font-semibold uppercase tracking-[0.15em] text-muted/50">Danger Zone</span>

			<div class="relative grid [&>*]:col-start-1 [&>*]:row-start-1">
				<div class="transition-all duration-200 {state === 'idle' ? 'opacity-100' : 'pointer-events-none opacity-0'}">
					<button
						class="w-full rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-2.5 text-sm font-medium text-red-600 dark:text-red-400 transition-colors hover:bg-red-500/20"
						onclick={() => (state = 'confirm')}
					>
						Delete All Progress
					</button>
				</div>

				<div class="space-y-3 transition-all duration-200 {state === 'confirm' ? 'opacity-100' : 'pointer-events-none opacity-0'}">
					<p class="text-sm text-text">Delete all book progress?</p>
					<div class="flex gap-2">
						<button
							class="rounded-lg bg-red-500 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-red-600"
							onclick={handleDelete}
						>
							Yes, delete
						</button>
						<button
							class="rounded-lg border border-text/[0.08] dark:border-white/[0.08] px-3 py-1.5 text-sm font-medium text-muted transition-colors hover:text-text"
							onclick={() => (state = 'idle')}
						>
							Cancel
						</button>
					</div>
				</div>

				<div class="flex items-center transition-all duration-200 {state === 'feedback' ? 'opacity-100' : 'pointer-events-none opacity-0'}">
					<p class="text-sm font-medium text-green-600 dark:text-green-400">Progress deleted</p>
				</div>
			</div>
		</div>
	</div>
{/if}
