import { writable } from 'svelte/store';
import { browser } from '$app/environment';

const NAME_KEY = 'lectorius_user';
const UNLOCKED_KEY = 'lectorius_unlocked';

function createUserNameStore() {
	const initial = browser ? localStorage.getItem(NAME_KEY) || '' : '';
	const { subscribe, set } = writable(initial);

	return {
		subscribe,
		setName(name: string) {
			if (browser) localStorage.setItem(NAME_KEY, name);
			set(name);
		}
	};
}

function createUnlockedStore() {
	const initial = browser ? localStorage.getItem(UNLOCKED_KEY) === 'true' : false;
	const { subscribe, set } = writable(initial);

	return {
		subscribe,
		unlock() {
			if (browser) localStorage.setItem(UNLOCKED_KEY, 'true');
			set(true);
		}
	};
}

export const userName = createUserNameStore();
export const unlocked = createUnlockedStore();
