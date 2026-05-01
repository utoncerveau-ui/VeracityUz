// Theme Management for Veracity Uz
// Handles system preference, localStorage persistence, and toggle logic

const applyTheme = (theme) => {
    if (theme === 'dark') {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }
};

const initTheme = () => {
    const savedTheme = localStorage.getItem('veracity_theme');
    if (savedTheme) {
        applyTheme(savedTheme);
    } else {
        const systemPref = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        applyTheme(systemPref);
    }
};

const toggleTheme = () => {
    const isDark = document.documentElement.classList.contains('dark');
    const newTheme = isDark ? 'light' : 'dark';
    applyTheme(newTheme);
    localStorage.setItem('veracity_theme', newTheme);
};

// Check theme immediately to avoid flash of light mode
initTheme();

document.addEventListener("DOMContentLoaded", () => {
    // Re-check in case DOM updates affect classes
    initTheme();
    
    // Wire up any toggle buttons found in the DOM
    const toggles = document.querySelectorAll('.theme-toggle');
    toggles.forEach(btn => {
        btn.addEventListener('click', toggleTheme);
    });
});
