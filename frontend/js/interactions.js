// Tab switching logic (Phase 4 Restoration)
document.addEventListener("DOMContentLoaded", () => {
    const tabText = document.getElementById('tabText');
    const tabLink = document.getElementById('tabLink');
    const textContainer = document.getElementById('textInputContainer');
    const urlContainer = document.getElementById('urlInputContainer');

    if (tabText && tabLink) {
        tabText.addEventListener('click', () => {
            textContainer.classList.remove('hidden');
            urlContainer.classList.add('hidden');
            tabText.classList.add('border-b-2', 'border-primary', 'dark:border-blue-400', 'text-primary', 'dark:text-white');
            tabText.classList.remove('text-secondary', 'dark:text-slate-400');
            tabLink.classList.remove('border-b-2', 'border-primary', 'dark:border-blue-400', 'text-primary', 'dark:text-white');
            tabLink.classList.add('text-secondary', 'dark:text-slate-400');
        });

        tabLink.addEventListener('click', () => {
            urlContainer.classList.remove('hidden');
            textContainer.classList.add('hidden');
            tabLink.classList.add('border-b-2', 'border-primary', 'dark:border-blue-400', 'text-primary', 'dark:text-white');
            tabLink.classList.remove('text-secondary', 'dark:text-slate-400');
            tabText.classList.remove('border-b-2', 'border-primary', 'dark:border-blue-400', 'text-primary', 'dark:text-white');
            tabText.classList.add('text-secondary', 'dark:text-slate-400');
        });
    }
});
