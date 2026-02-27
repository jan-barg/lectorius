import { writable } from 'svelte/store';
import { browser } from '$app/environment';

const NAME_KEY = 'lectorius_user';

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

export const userName = createUserNameStore();
