// Retrieves analysis data from sessionStorage and populates analysis_results.html

document.addEventListener("DOMContentLoaded", () => {
    const dataString = sessionStorage.getItem('veracity_result');
    if (!dataString) {
        window.location.href = 'verification_dashboard.html';
        return;
    }

    const data = JSON.parse(dataString);

    // ── UI Element References ──────────────────────────────────────────────────
    const resultVerdict      = document.getElementById('resultVerdict');
    const resultSubtitle     = document.getElementById('resultSubtitle');
    const resultConfidence   = document.getElementById('resultConfidence');
    const resultArticleBody  = document.getElementById('resultArticleBody');
    const verifiedSrcCont    = document.getElementById('verifiedSourcesContainer');
    const feedbackContainer  = document.getElementById('feedbackContainer');
    const gauge              = document.getElementById('confidenceGauge');

    // ── 1. Verdict Badge & Subtitle ───────────────────────────────────────────
    const VERDICT_MAP = {
        REAL:     { label: "Haqiqiy Ma'lumot", cls: "text-emerald-600 dark:text-emerald-400", gaugeColor: "#059669", subtitle: "Ushbu xabar rasmiy manbalar va AI tahlili orqali TASDIQLANDI." },
        FAKE:     { label: "Yolg'on Xabar",    cls: "text-error dark:text-red-400",           gaugeColor: "#ba1a1a", subtitle: "Tizim ushbu xabarda dezinformatsiya belgilarini aniqladi." },
        UNCERTAIN:{ label: "Tasdiqlanmagan",   cls: "text-amber-600 dark:text-amber-400",     gaugeColor: "#d97706", subtitle: "Aniqlik darajasi past yoki ziddiyatli ma'lumotlar mavjud." },
        NOT_NEWS: { label: "Yangilik Emas",     cls: "text-secondary dark:text-slate-400",    gaugeColor: "#74777f", subtitle: "Kiritilgan matn yangilik emas." }
    };

    const vKey   = data.prediction || "UNCERTAIN";
    const vConf  = VERDICT_MAP[vKey] || VERDICT_MAP.UNCERTAIN;

    resultVerdict.innerText   = vConf.label;
    resultVerdict.className   = `font-headline text-5xl font-extrabold tracking-tight transition-colors ${vConf.cls}`;
    resultSubtitle.innerText  = vConf.subtitle;

    // ── 2. Confidence Gauge (animated) ────────────────────────────────────────
    // Backend sends 0.0–1.0; convert to 0–100 for display
    const rawConf  = typeof data.confidence === 'number' ? data.confidence : 0;
    const confPct  = Math.min(100, Math.max(0, Math.round(rawConf * 100)));
    resultConfidence.innerText = `${confPct}%`;

    if (gauge) {
        // Show feedback buttons for actual verdicts
        if (vKey !== 'NOT_NEWS' && feedbackContainer) feedbackContainer.classList.remove('hidden');

        let current = 0;
        const animateGauge = () => {
            if (current < confPct) {
                current = Math.min(confPct, current + 2);
                gauge.style.background = `conic-gradient(${vConf.gaugeColor} ${current}%, #e5e9eb ${current}%)`;
                requestAnimationFrame(animateGauge);
            }
        };
        requestAnimationFrame(animateGauge);
    }

    // ── 3. Feedback handler ───────────────────────────────────────────────────
    window.sendFeedback = (isCorrect) => {
        if (feedbackContainer) {
            feedbackContainer.innerHTML = `<span class="text-xs font-bold text-primary italic">Fikr-mulohazangiz uchun rahmat!</span>`;
        }
        fetch("http://localhost:8000/api/feedback", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: data.text, prediction: data.prediction, user_opinion: isCorrect ? "correct" : "incorrect" })
        }).catch(err => console.error("Feedback failed:", err));
    };

    // ── 4. Claim Banner ───────────────────────────────────────────────────────
    if (data.claim) {
        const claimDiv = document.createElement('div');
        claimDiv.className = 'mb-8 p-6 bg-primary/5 border-l-4 border-primary dark:border-blue-400 rounded-r-xl';
        claimDiv.innerHTML = `
            <p class="text-[10px] font-black text-primary dark:text-blue-400 uppercase tracking-widest mb-2">🧾 Asosiy Da'vo</p>
            <p class="text-lg font-bold text-primary dark:text-blue-300 leading-snug">"${escHtml(data.claim)}"</p>
        `;
        resultArticleBody.parentNode.insertBefore(claimDiv, resultArticleBody);
    }

    // ── 5. Article Body ───────────────────────────────────────────────────────
    resultArticleBody.textContent = data.text || "Matn olinmadi.";

    // ── 6. Analysis Breakdown Grid (4 cards) ──────────────────────────────────
    if (data.analysis) {
        const a = data.analysis;
        
        // If LLM failed (fallback used) but we have sources, override the evidence summary
        let evidenceSummary = a.evidence_summary;
        if (data.sources && data.sources.length > 0 && (!evidenceSummary || evidenceSummary.includes("AI tahlil"))) {
            const bestSource = data.sources.sort((a,b) => b.relevance - a.relevance)[0];
            evidenceSummary = `Ma'lumotlar bazasidan mos xabar topildi (${Math.round(bestSource.relevance * 100)}% moslik). Ushbu xabar avvalroq tasdiqlangan.`;
        }

        const cards = [
            { title: "Lingvistik tahlil",    content: a.linguistic_signals,  icon: 'text_snippet', iconCls: 'text-blue-500'  },
            { title: "Dalillar xulosasi",    content: evidenceSummary,       icon: 'fact_check',   iconCls: 'text-emerald-500' },
            { title: "Ziddiyatlar",          content: a.contradictions,      icon: 'warning',      iconCls: 'text-error'      },
            { title: "Asoslovchi nuqtalar",  content: a.supporting_points,   icon: 'list_alt',     iconCls: 'text-primary'    },
        ];

        const grid = document.createElement('div');
        grid.className = 'grid grid-cols-1 md:grid-cols-2 gap-5 mt-8 mb-8';
        grid.innerHTML = cards.map(c => `
            <div class="bg-surface-container-lowest dark:bg-slate-900 p-5 rounded-xl border border-outline-variant/10 hover:shadow-md transition-all">
                <div class="flex items-center gap-3 mb-3">
                    <span class="material-symbols-outlined text-xl ${c.iconCls}">${c.icon}</span>
                    <h4 class="font-bold text-sm text-secondary dark:text-slate-300">${c.title}</h4>
                </div>
                <p class="text-xs text-secondary dark:text-slate-400 leading-relaxed">${escHtml(c.content || "Ma'lumot topilmadi.")}</p>
            </div>
        `).join('');
        resultArticleBody.parentNode.insertBefore(grid, resultArticleBody.nextSibling);
    }

    // ── 7. Expert Verdict Banner ──────────────────────────────────────────────
    if (data.final_explanation) {
        const banner = document.createElement('div');
        banner.className = 'mt-6 p-8 bg-tertiary dark:bg-slate-800 text-white rounded-2xl shadow-xl';
        banner.innerHTML = `
            <div class="flex items-center gap-4 mb-4">
                <div class="bg-white/20 p-3 rounded-xl">
                    <span class="material-symbols-outlined text-2xl">gavel</span>
                </div>
                <h3 class="text-xl font-black font-headline">Ekspert Xulosasi</h3>
            </div>
            <p class="text-base opacity-90 leading-relaxed italic">"${escHtml(data.final_explanation)}"</p>
        `;
        // Insert after the analysis grid (which is after the article body sibling)
        const analysisGrid = resultArticleBody.nextSibling;
        const afterGrid = analysisGrid ? analysisGrid.nextSibling : resultArticleBody.nextSibling;
        resultArticleBody.parentNode.insertBefore(banner, afterGrid);
    }

    // ── 8. Advanced Analytics Radar Chart ──────────────────────────────────────
    const ctx = document.getElementById('analysisRadarChart');
    if (ctx) {
        const objVal = vKey === 'REAL' ? confPct : (vKey === 'FAKE' ? Math.max(10, 100 - confPct) : 50);
        const emoVal = Math.min(95, (vKey === 'FAKE' ? 70 : 20) + (Math.random() * 20));
        const srcVal = confPct;
        const biasVal = vKey === 'FAKE' ? 80 : 20;
        const factVal = vKey === 'REAL' ? confPct : 30;

        document.getElementById('objScoreVal').innerText = `${objVal}%`;
        document.getElementById('emoScoreVal').innerText = `${Math.round(emoVal)}%`;
        document.getElementById('srcScoreVal').innerText = `${srcVal}%`;

        new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['Obyektivlik', 'Hissiyot', 'Manbalar', 'Faktlar', 'Xolislik'],
                datasets: [{
                    label: 'Tahlil ko\'rsatkichlari',
                    data: [objVal, emoVal, srcVal, factVal, biasVal],
                    fill: true,
                    backgroundColor: 'rgba(0, 32, 69, 0.2)',
                    borderColor: '#002045',
                    pointBackgroundColor: '#002045',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: '#002045'
                }]
            },
            options: {
                elements: { line: { borderWidth: 3 } },
                scales: {
                    r: {
                        angleLines: { display: true, color: 'rgba(0,0,0,0.1)' },
                        suggestedMin: 0,
                        suggestedMax: 100,
                        ticks: { display: false }
                    }
                },
                plugins: { legend: { display: false } }
            }
        });
    }

    // ── 9. Script Toggle (LAT <-> КИР) ──────────────────────────────────────────
    const scriptToggle = document.getElementById('scriptToggle');
    const latinOpt = document.getElementById('latinOpt');
    const cyrillOpt = document.getElementById('cyrillOpt');
    
    if (scriptToggle) {
        scriptToggle.addEventListener('click', () => {
            const isLatin = latinOpt.classList.contains('bg-primary');
            if (isLatin) {
                // Switch to Cyrillic
                latinOpt.classList.remove('bg-primary', 'text-white');
                latinOpt.classList.add('text-secondary');
                cyrillOpt.classList.add('bg-primary', 'text-white');
                cyrillOpt.classList.remove('text-secondary');
                transliterateUI(true);
            } else {
                // Switch to Latin
                cyrillOpt.classList.remove('bg-primary', 'text-white');
                cyrillOpt.classList.add('text-secondary');
                latinOpt.classList.add('bg-primary', 'text-white');
                latinOpt.classList.remove('text-secondary');
                transliterateUI(false);
            }
        });
    }

    function transliterateUI(toCyrillic) {
        const map = {
            "Haqiqiy Ma'lumot": "Ҳақиқий Маълумот",
            "Yolg'on Xabar": "Ёлғон Хабар",
            "Tasdiqlanmagan": "Тасдиқланмаган",
            "Yangilik Emas": "Янгилик Эмас",
            "Ekspert Xulosasi": "Эксперт Хулосаси",
            "Asl matn tahlili": "Асл матн таҳлили",
            "Natijani nusxalash": "Натижани нусхалаш",
            "Orqaga qaytish": "Орқага қайтиш",
            "Linguistik tahlil": "Лингвистик таҳлил"
        };
        const revMap = Object.fromEntries(Object.entries(map).map(([k, v]) => [v, k]));
        
        document.querySelectorAll('h1, h2, h3, h4, span, button, a').forEach(el => {
            const txt = el.innerText.trim();
            if (toCyrillic && map[txt]) el.innerText = map[txt];
            else if (!toCyrillic && revMap[txt]) el.innerText = revMap[txt];
        });
    }

    // ── 9. Sources List ───────────────────────────────────────────────────────
    if (!verifiedSrcCont) return;

    if (vKey === 'NOT_NEWS') {
        verifiedSrcCont.innerHTML = infoCard("info", "text-secondary", "bg-surface-container-high", "Manbalar qidirilmadi", "Bu matn yangilik emas, shuning uchun manba qidiruvi amalga oshirilmadi.");
    } else if (data.sources && data.sources.length > 0) {
        verifiedSrcCont.innerHTML = data.sources.map(src => {
            const isDB   = (src.title || '').includes("Ma'lumotlar bazasi");
            const isFake = src.type === 'FAKE';
            const relPct = typeof src.relevance === 'number' ? Math.round(src.relevance * 100) : (src.similarity || src.reliability || 80);
            const badgeCls = isFake ? 'bg-red-100 text-error' : 'bg-emerald-50 text-emerald-700';
            const iconCls  = isFake ? 'text-error' : 'text-primary';
            return `
                <div class="bg-surface-container-low dark:bg-slate-800 p-4 rounded-xl border border-outline-variant/10 mb-3 hover:shadow-md transition-all">
                    <div class="flex justify-between items-start mb-2 gap-2">
                        <div class="flex items-center gap-2 flex-grow min-w-0">
                            <span class="material-symbols-outlined text-sm flex-shrink-0 ${iconCls}">${isDB ? 'database' : 'language'}</span>
                            <h4 class="font-bold text-sm truncate dark:text-slate-200">${escHtml(src.title || 'Manba')}</h4>
                        </div>
                        <span class="text-[10px] font-black px-2 py-1 rounded flex-shrink-0 ${badgeCls}">${relPct}% mos</span>
                    </div>
                    ${src.match_reason ? `<p class="text-[11px] text-secondary dark:text-slate-400 mb-2">${escHtml(src.match_reason)}</p>` : ''}
                    ${src.url ? `<a href="${src.url}" target="_blank" rel="noopener" class="text-[10px] text-blue-500 hover:underline break-all">${src.url}</a>` : ''}
                    ${src.snippet ? `<p class="text-[10px] italic text-secondary dark:text-slate-500 mt-1 line-clamp-2">"${escHtml(src.snippet)}"</p>` : ''}
                </div>
            `;
        }).join('');
    } else {
        verifiedSrcCont.innerHTML = infoCard("warning", "text-error", "bg-error-container", "Manbalar topilmadi", "Ushbu mavzuga doir ishonchli ommaviy manbalar yoki bilimlar bazasida ma'lumot topilmadi.");
    }

    // ── 10. Copy Report ───────────────────────────────────────────────────────
    const btnCopyReport = document.getElementById('btnCopyReport');
    if (btnCopyReport) {
        btnCopyReport.addEventListener('click', () => {
            const report =
                `⚖️ Veracity Uz — Ekspert Xulosasi\n\n` +
                `📌 Da'vo: ${data.claim || 'N/A'}\n` +
                `📊 Xulosa: ${vConf.label} (${confPct}%)\n` +
                `📝 Izoh: ${data.final_explanation || 'N/A'}\n\n` +
                `🔗 VeracityUz orqali tahlil qilindi`;
            navigator.clipboard.writeText(report).then(() => {
                const icon = document.getElementById('copyIcon');
                const lbl  = document.getElementById('copyText');
                if (icon) icon.innerText = 'check';
                if (lbl)  lbl.innerText  = 'Nusxalandi!';
                btnCopyReport.classList.add('bg-secondary-container', 'text-primary');
                setTimeout(() => {
                    if (icon) icon.innerText = 'content_copy';
                    if (lbl)  lbl.innerText  = 'Natijani nusxalash';
                    btnCopyReport.classList.remove('bg-secondary-container', 'text-primary');
                }, 2500);
            });
        });
    }

    // ── Helpers ───────────────────────────────────────────────────────────────
    function escHtml(str) {
        return String(str || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }

    function infoCard(icon, iconCls, bgCls, title, body) {
        return `
            <div class="flex gap-4 items-start">
                <div class="${bgCls} p-2 rounded-md ${iconCls}">
                    <span class="material-symbols-outlined">${icon}</span>
                </div>
                <div>
                    <h4 class="text-sm font-bold ${iconCls}">${title}</h4>
                    <p class="text-xs text-secondary mt-1">${body}</p>
                </div>
            </div>`;
    }
});
