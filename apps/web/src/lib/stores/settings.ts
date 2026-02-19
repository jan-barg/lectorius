import { writable } from 'svelte/store';
import { browser } from '$app/environment';

export type Theme = 'system' | 'light' | 'dark';

interface Settings {
    theme: Theme;
}

const defaultSettings: Settings = {
    theme: 'system'
};

function createSettingsStore() {
    const stored = browser ? localStorage.getItem('lectorius_theme') : null;
    const initialTheme: Theme = stored === 'light' || stored === 'dark' ? stored : 'system';

    const { subscribe, set, update } = writable<Settings>({ theme: initialTheme });

    return {
        subscribe,
        setTheme: (theme: Theme) => {
            if (browser) {
                localStorage.setItem('lectorius_theme', theme);
                update((s) => ({ ...s, theme }));
                applyTheme(theme);
            }
        },
        init: () => {
            if (browser) {
                const current = get(settings).theme;
                applyTheme(current);

                // Listen for system preference changes if in system mode
                window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
                    if (get(settings).theme === 'system') {
                        applyTheme('system');
                    }
                });
            }
        }
    };
}

// Helper to apply theme to document
function applyTheme(theme: Theme) {
    if (!browser) return;

    const isDark =
        theme === 'dark' ||
        (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);

    if (isDark) {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }
}

// Need to import get locally or define outside if not available (Svelte store 'get' utility)
import { get } from 'svelte/store';

export const settings = createSettingsStore();
