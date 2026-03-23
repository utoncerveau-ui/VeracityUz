// Retrieves analysis data from sessionStorage and populates analysis_results.html

document.addEventListener("DOMContentLoaded", () => {
    const dataString = sessionStorage.getItem('veracity_result');
    if (!dataString) {
        // If there's no result in local storage, go back to dashboard
        window.location.href = 'verification_dashboard.html';
        return;
    }

    const data = JSON.parse(dataString);
    
    // UI Elements
    const resultVerdict = document.getElementById('resultVerdict');
    const resultSubtitle = document.getElementById('resultSubtitle');
    const resultConfidence = document.getElementById('resultConfidence');
    const resultArticleBody = document.getElementById('resultArticleBody');
    const verifiedSourcesContainer = document.getElementById('verifiedSourcesContainer');
    
    // Dynamic Chips and Counts
    const spanConfirmedCount = document.getElementById('spanConfirmedCount');
    const spanSuspiciousCount = document.getElementById('spanSuspiciousCount');
    const chipConfirmed = document.getElementById('chipConfirmed');
    const chipSuspicious = document.getElementById('chipSuspicious');

    let confirmedCount = 0;
    let suspiciousCount = 0;

    // 1. Determine Verdict (Hybrid Logic)
    if (data.prediction === "NOT_NEWS") {
        resultVerdict.innerText = "Yangilik Emas";
        resultVerdict.className = "font-headline text-5xl font-extrabold text-secondary tracking-tight";
        resultSubtitle.innerText = "Kiritilgan matn yangilik emas. Iltimos, yangilik maqolasi yoki xabar matni kiriting.";
    } else if (data.found) {
        // Source Override: If found in trusted sources, it's REAL regardless of ML prediction
        resultVerdict.innerText = "Haqiqiy Ma'lumot";
        resultVerdict.className = "font-headline text-5xl font-extrabold text-[#1a5f7a] dark:text-blue-400 tracking-tight";
        resultSubtitle.innerText = data.prediction === "REAL" 
            ? "Ushbu xabar Sun'iy Intellekt va rasmiy manbalar orqali tasdiqlandi."
            : "Sun'iy Intellekt shubha qilgan bo'lsada, rasmiy manbalar xabarni tasdiqladi.";
    } else if (data.prediction === "REAL") {
        // Unverified: ML says real but NO sources found
        resultVerdict.innerText = "Tasdiqlanmagan";
        resultVerdict.className = "font-headline text-5xl font-extrabold text-amber-600 dark:text-amber-400 tracking-tight";
        resultSubtitle.innerText = "Matn mantiqiy ko'rinadi, lekin ishonchli manbalarda tasdig'i topilmadi. Ehtiyot bo'ling.";
    } else {
        // Fake: ML says fake and no sources found
        resultVerdict.innerText = "Yolg'on Xabar";
        resultVerdict.className = "font-headline text-5xl font-extrabold text-error tracking-tight";
        resultSubtitle.innerText = "Diqqat: Ushbu matn dezinformatsiya belgilarini ko'rsatmoqda va manbalar topilmadi.";
    }

    if (data.prediction === "NOT_NEWS") {
        resultConfidence.innerText = `N/A`;
        resultConfidence.className = "font-headline text-2xl font-bold text-secondary";
    } else {
        resultConfidence.innerText = `${(data.confidence * 100).toFixed(0)}%`;
    }
    
    function highlightText(text, sources) {
        if (!text) return "Matn olinmadi.";
        let highlighted = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        
        // 1. Highlight Buzzwords (Suspicious - Red)
        const buzzwords = ["SHOK", "DAHSHAT", "SENSATSIYA", "SHOSHILINCH", "DIQQAT", "YOLG'ON", "SIRLAR", "FOSH", "SHOK XABAR", "FAVQULODDA"];
        buzzwords.forEach(word => {
            const regex = new RegExp(`(${word})`, 'gi');
            highlighted = highlighted.replace(regex, (match) => {
                suspiciousCount++;
                return `<span class="px-1 bg-error-container/40 text-error border-b-2 border-error font-bold">${match}</span>`;
            });
        });

        // 2. Highlight Trusted Entities (Verified - Blue)
        const trustedEntities = ["Kun.uz", "Daryo", "Gazeta.uz", "UZA", "Sputnik", "Podrobno", "Xabar.uz", "Qalampir", "UzNews", "Spot"];
        
        if (sources && sources.length > 0) {
            sources.forEach(src => {
                const words = src.title.split(' ').filter(w => w.length > 5);
                words.slice(0, 3).forEach(w => {
                    const cleanW = w.replace(/[.,\/#!$%\^&\*;:{}=\-_`~()]/g,"");
                    if (cleanW.length > 3 && !trustedEntities.includes(cleanW)) trustedEntities.push(cleanW);
                });
            });
        }

        trustedEntities.forEach(entity => {
            if (entity.length < 3) return;
            const escapedEntity = entity.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            const regex = new RegExp(`(${escapedEntity})`, 'gi');
            
            highlighted = highlighted.replace(regex, (match, p1, offset, string) => {
                const prevTag = string.substring(0, offset).lastIndexOf('<span');
                const lastClose = string.substring(0, offset).lastIndexOf('</span>');
                if (prevTag > lastClose) return match; 
                
                confirmedCount++;
                return `<span class="px-1 bg-secondary-container/40 text-primary border-b-2 border-primary font-bold">${p1}</span>`;
            });
        });

        return highlighted;
    }

    if (data.text) {
        resultArticleBody.innerHTML = highlightText(data.text, data.sources);
        // Update chip counts
        spanConfirmedCount.innerText = `${confirmedCount} ta Tasdiqlangan`;
        spanSuspiciousCount.innerText = `${suspiciousCount} ta Shubhali qism`;
        
        // Reveal chips
        chipConfirmed.classList.remove('opacity-50');
        chipSuspicious.classList.remove('opacity-50');
    } else {
        resultArticleBody.innerText = "Matn olinmadi.";
    }

    // Populate Linguistics
    const objScore = document.getElementById('objScore');
    const objBar = document.getElementById('objBar');
    const emoScore = document.getElementById('emoScore');
    const emoBar = document.getElementById('emoBar');
    const srcScore = document.getElementById('srcScore');
    const srcBar = document.getElementById('srcBar');

    setTimeout(() => {
        if (data.prediction === "NOT_NEWS") {
            objScore.innerText = `N/A`;
            emoScore.innerText = `N/A`;
            srcScore.innerText = `N/A`;
            return;
        }

        if (data.linguistics) {
            objScore.innerText = `${data.linguistics.objectivity}%`;
            objBar.style.width = `${data.linguistics.objectivity}%`;

            let emoLabel = data.linguistics.emotional < 30 ? 'Past' : data.linguistics.emotional < 70 ? "O'rta" : 'Yuqori';
            emoScore.innerText = `${emoLabel} (${data.linguistics.emotional}%)`;
            emoBar.style.width = `${data.linguistics.emotional}%`;
        }

        const accuracy = data.found ? 100 : Math.round(data.confidence * 100);
        srcScore.innerText = `${accuracy}%`;
        srcBar.style.width = `${accuracy}%`;
    }, 150);

    // Populate Sources
    if (data.prediction === 'NOT_NEWS') {
        verifiedSourcesContainer.innerHTML = `
        <div class="flex gap-4 items-start">
            <div class="bg-surface-container-high p-2 rounded-sm text-secondary">
                <span class="material-symbols-outlined">info</span>
            </div>
            <div>
                <h4 class="text-sm font-bold text-secondary">Manbalar qidirilmadi</h4>
                <p class="text-xs text-secondary mt-1">Bu matn yangilik emas, shuning uchun manba qidiruvi amalga oshirilmadi.</p>
            </div>
        </div>`;
    } else if (data.found && data.sources && data.sources.length > 0) {
        verifiedSourcesContainer.innerHTML = '';
        data.sources.forEach(source => {
            verifiedSourcesContainer.innerHTML += `
            <div class="flex gap-4 items-start mb-4">
                <div class="bg-secondary-container p-2 rounded-sm text-primary">
                    <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">verified</span>
                </div>
                <div>
                    <h4 class="text-sm font-bold text-tertiary"><a href="${source.url}" target="_blank" class="hover:underline">${source.title}</a></h4>
                    <p class="text-xs text-secondary mt-1 overflow-hidden text-ellipsis whitespace-nowrap max-w-xs">${source.url}</p>
                </div>
            </div>`;
        });
    } else {
        verifiedSourcesContainer.innerHTML = `
        <div class="flex gap-4 items-start">
            <div class="bg-error-container p-2 rounded-sm text-error">
                <span class="material-symbols-outlined">warning</span>
            </div>
            <div>
                <h4 class="text-sm font-bold text-error">Manbalar topilmadi</h4>
                <p class="text-xs text-secondary mt-1">Ushbu mavzuga doir ishonchli ommaviy manbalar topilmadi.</p>
            </div>
        </div>`;
    }
});
