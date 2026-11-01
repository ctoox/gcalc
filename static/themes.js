class ThemeManager {
    constructor() {
        this.themes = {
            cosmic: { bg: '#0a0a2e', text: '#e0e0ff', accent: '#4466cc' },
            dark: { bg: '#1a1a2e', text: '#eee', accent: '#cc4466' },
            light: { bg: '#f0f0ff', text: '#333', accent: '#4466cc' }
        };
        this.current = 'cosmic';
        this.load();
    }

    load() {
        const saved = localStorage.getItem('gcalc-theme');
        if (saved && this.themes[saved]) {
            this.apply(saved);
        }
    }

    apply(name) {
        const theme = this.themes[name];
        if (!theme) return;
        document.body.style.setProperty('--bg', theme.bg);
        document.body.style.setProperty('--text', theme.text);
        document.body.style.setProperty('--accent', theme.accent);
        this.current = name;
        localStorage.setItem('gcalc-theme', name);
    }

    toggle() {
        const names = Object.keys(this.themes);
        const idx = (names.indexOf(this.current) + 1) % names.length;
        this.apply(names[idx]);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const tm = new ThemeManager();
    const toggleBtn = document.getElementById('theme-toggle');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => tm.toggle());
    }
});
