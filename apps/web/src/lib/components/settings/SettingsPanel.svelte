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
		class="fixed inset-0 z-40 bg-black/40 dark:bg-black/60 backdrop-blur-sm"
		onclick={onClose}
		aria-label="Close settings"
		transition:fade={{ duration: 300 }}
	></button>

	<!-- Panel -->
	<div
		class="fixed top-0 right-0 z-50 h-full w-[22rem] bg-background/95 backdrop-blur-2xl border-l border-text/[0.05] dark:border-white/[0.05] p-8 shadow-2xl shadow-black/15 dark:shadow-black/40"
		transition:fly={{ x: 360, duration: 350, opacity: 1 }}
	>
		<div class="mb-10 flex items-center justify-between">
			<h2 class="font-display text-xl font-light text-text tracking-tight">Settings</h2>
			<button class="flex h-9 w-9 items-center justify-center rounded-xl text-muted hover:text-text hover:bg-text/[0.04] dark:hover:bg-white/[0.04] transition-all duration-300" onclick={onClose} aria-label="Close">
				<svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
				</svg>
			</button>
		</div>

		<div class="space-y-6">
			<div>
				<span class="mb-2.5 block text-[10px] font-bold uppercase tracking-[0.2em] text-muted/50">Name</span>
				<input
					type="text"
					bind:value={nameInput}
					onblur={handleNameBlur}
					onkeydown={(e) => e.key === 'Enter' && e.currentTarget.blur()}
					class="w-full rounded-xl border border-text/[0.06] dark:border-white/[0.06] bg-text/[0.02] dark:bg-white/[0.02] px-4 py-3 text-sm text-text placeholder:text-muted/30 outline-none focus:border-accent/30 focus:ring-2 focus:ring-accent/8 transition-all duration-300"
					placeholder="Enter your name"
				/>
			</div>

			<div>
				<span class="mb-2.5 block text-[10px] font-bold uppercase tracking-[0.2em] text-muted/50">Theme</span>
				<ThemeSwitcher />
			</div>

			<div>
				<span class="mb-2.5 block text-[10px] font-bold uppercase tracking-[0.2em] text-muted/50">Questions Access</span>
				{#if codeSuccess}
					<div class="flex items-center gap-2.5 rounded-xl bg-green-500/[0.06] dark:bg-green-400/[0.06] border border-green-500/10 dark:border-green-400/10 px-4 py-2.5">
						<div class="flex h-5 w-5 items-center justify-center rounded-full bg-green-500/15 dark:bg-green-400/15">
							<svg class="h-3 w-3 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
							</svg>
						</div>
						<span class="text-sm font-medium text-green-700 dark:text-green-400">Unlimited</span>
					</div>
				{:else}
					<div class="space-y-2.5">
						<input
							type="text"
							bind:value={codeInput}
							onkeydown={(e) => e.key === 'Enter' && handleVerifyCode()}
							placeholder="Enter access code"
							class="w-full rounded-xl border border-text/[0.06] dark:border-white/[0.06] bg-text/[0.02] dark:bg-white/[0.02] px-4 py-3 text-sm text-text placeholder:text-muted/30 outline-none focus:border-accent/30 focus:ring-2 focus:ring-accent/8 transition-all duration-300"
						/>
						<button
							onclick={handleVerifyCode}
							disabled={!codeInput.trim() || codeLoading}
							class="w-full rounded-xl bg-accent px-4 py-3 text-sm font-semibold text-white shadow-md shadow-accent/15 transition-all duration-300 hover:brightness-110 hover:shadow-lg hover:shadow-accent/20 disabled:opacity-30 disabled:shadow-none"
						>
							{codeLoading ? 'Verifying...' : 'Unlock'}
						</button>
						{#if codeError}
							<p class="text-xs text-red-400/80 font-medium">{codeError}</p>
						{/if}
					</div>
				{/if}
			</div>
		</div>

		<!-- Danger zone -->
		<div class="mt-14 border-t border-text/[0.05] dark:border-white/[0.05] pt-7">
			<span class="mb-4 block text-[10px] font-bold uppercase tracking-[0.2em] text-muted/40">Danger Zone</span>

			<div class="relative grid [&>*]:col-start-1 [&>*]:row-start-1">
				<div class="transition-all duration-300 {state === 'idle' ? 'opacity-100' : 'pointer-events-none opacity-0'}">
					<button
						class="w-full rounded-xl border border-red-500/15 bg-red-500/[0.06] px-4 py-3 text-sm font-medium text-red-600 dark:text-red-400 transition-all duration-300 hover:bg-red-500/[0.12] hover:border-red-500/25"
						onclick={() => (state = 'confirm')}
					>
						Delete All Progress
					</button>
				</div>

				<div class="space-y-3 transition-all duration-300 {state === 'confirm' ? 'opacity-100' : 'pointer-events-none opacity-0'}">
					<p class="text-sm text-text font-medium">Delete all book progress?</p>
					<div class="flex gap-2.5">
						<button
							class="rounded-xl bg-red-500 px-4 py-2 text-sm font-semibold text-white shadow-md shadow-red-500/20 transition-all duration-300 hover:bg-red-600 hover:shadow-lg"
							onclick={handleDelete}
						>
							Yes, delete
						</button>
						<button
							class="rounded-xl border border-text/[0.06] dark:border-white/[0.06] px-4 py-2 text-sm font-medium text-muted transition-all duration-300 hover:text-text hover:bg-text/[0.03] dark:hover:bg-white/[0.03]"
							onclick={() => (state = 'idle')}
						>
							Cancel
						</button>
					</div>
				</div>

				<div class="flex items-center transition-all duration-300 {state === 'feedback' ? 'opacity-100' : 'pointer-events-none opacity-0'}">
					<p class="text-sm font-medium text-green-600 dark:text-green-400">Progress deleted</p>
				</div>
			</div>
		</div>
	</div>
{/if}
