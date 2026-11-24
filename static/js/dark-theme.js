/**
 * Dark Theme Toggle
 * Handles dark mode switching with localStorage persistence
 */

class DarkThemeToggle {
    constructor() {
        this.storageKey = 'theme';
        this.darkModeClass = 'dark-mode';
        this.init();
    }

    init() {
        this.applyStoredTheme();
        this.setupToggleButton();
        this.watchSystemTheme();
    }

    applyStoredTheme() {
        const isDarkMode = this.isDarkModeEnabled();
        if (isDarkMode) {
            this.enableDarkMode();
        } else {
            this.disableDarkMode();
        }
    }

    isDarkModeEnabled() {
        const stored = localStorage.getItem(this.storageKey);
        if (stored !== null) {
            return stored === 'dark';
        }
        return window.matchMedia('(prefers-color-scheme: dark)').matches;
    }

    setupToggleButton() {
        const button = document.getElementById('theme-toggle-btn') || document.getElementById('themeToggle');
        if (button) {
            button.addEventListener('click', () => this.toggle());
        }
    }

    toggle() {
        const isDarkMode = document.body.classList.contains(this.darkModeClass);
        if (isDarkMode) {
            this.disableDarkMode();
        } else {
            this.enableDarkMode();
        }
    }

    enableDarkMode() {
        document.body.classList.add(this.darkModeClass);
        localStorage.setItem(this.storageKey, 'dark');
        this.updateToggleButton(true);
    }

    disableDarkMode() {
        document.body.classList.remove(this.darkModeClass);
        localStorage.setItem(this.storageKey, 'light');
        this.updateToggleButton(false);
    }

    updateToggleButton(isDarkMode) {
        const button = document.getElementById('theme-toggle-btn') || document.getElementById('themeToggle');
        if (button) {
            const icon = button.querySelector('i') || button.querySelector('svg');
            if (icon) {
                icon.classList.remove('bi-moon-fill', 'bi-sun-fill', 'bi-moon', 'bi-sun');
                if (isDarkMode) {
                    icon.classList.add('bi-sun-fill');
                    button.setAttribute('title', 'Switch to Light Mode');
                    button.setAttribute('aria-label', 'Switch to Light Mode');
                } else {
                    icon.classList.add('bi-moon-fill');
                    button.setAttribute('title', 'Switch to Dark Mode');
                    button.setAttribute('aria-label', 'Switch to Dark Mode');
                }
            }
        }
    }

    watchSystemTheme() {
        // Watch for system theme changes if no explicit user preference is set
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        mediaQuery.addEventListener('change', (e) => {
            const stored = localStorage.getItem(this.storageKey);
            // Only apply system theme if user hasn't explicitly set a preference
            if (stored === null) {
                if (e.matches) {
                    this.enableDarkMode();
                } else {
                    this.disableDarkMode();
                }
            }
        });
    }
}

// Initialize dark theme toggle when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new DarkThemeToggle();
    });
} else {
    // DOM is already loaded
    new DarkThemeToggle();
}
