// API fetching logic for the Verification Dashboard connecting to FastAPI
document.addEventListener("DOMContentLoaded", () => {
    const verifyBtn = document.getElementById('verifyBtn');
    
    if (verifyBtn) {
        verifyBtn.addEventListener('click', async () => {
            const btn = document.getElementById('verifyBtn');
            const originalBtnHTML = btn.innerHTML;
            const text = document.getElementById('textInput').value;
            const resultsContainer = document.getElementById('resultsContainer');
            const mlResult = document.getElementById('mlResult');
            const verifyResult = document.getElementById('verifyResult');
            
            if (!text) {
                alert("Iltimos, tahlil qilish uchun matn kiriting.");
                return;
            }

            btn.disabled = true;
            btn.classList.add('opacity-50', 'cursor-not-allowed');
            btn.innerHTML = `<span class="material-symbols-outlined animate-spin" data-icon="sync">sync</span> Tahlil qilinmoqda...`;

            // Reset and show stepper
            resultsContainer.classList.remove('hidden');
            const steps = [1, 2, 3, 4].map(i => document.getElementById(`step${i}`));
            steps.forEach(s => { s.classList.add('opacity-30'); s.classList.remove('opacity-100'); });
            
            const activateStep = (i) => {
                if (steps[i-1]) {
                    steps[i-1].classList.remove('opacity-30');
                    steps[i-1].classList.add('opacity-100');
                    const icon = steps[i-1].querySelector('.step-icon');
                    if (icon) icon.classList.add('ring-4', 'ring-primary/20', 'dark:ring-blue-400/20');
                }
            };

            activateStep(1); // Start with step 1
            setTimeout(() => activateStep(2), 800);
            setTimeout(() => activateStep(3), 2000);
            setTimeout(() => activateStep(4), 4500);

            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 45000);

            try {
                const predRes = await fetch("http://localhost:8000/api/predict", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({text: text}),
                    signal: controller.signal
                });
                
                if (predRes.ok) {
                    const predData = await predRes.json();
                    
                    clearTimeout(timeoutId);

                    sessionStorage.setItem('veracity_result', JSON.stringify({
                        prediction: predData.verdict || predData.prediction,
                        confidence: predData.confidence,
                        text: text || predData.text,
                        found: predData.sources && predData.sources.some(s => s.url),
                        sources: predData.sources,
                        claim: predData.claim,
                        analysis: predData.analysis,
                        final_explanation: predData.final_explanation,
                        explanation: predData.final_explanation || predData.explanation,
                        linguistics: predData.linguistics
                    }));

                    window.location.href = 'analysis_results.html';
                }
 else {
                    clearTimeout(timeoutId);
                    const err = await predRes.json();
                    throw new Error(err.detail || "Server error");
                }
            } catch (e) {
                clearTimeout(timeoutId);
                resultsContainer.classList.remove('hidden');
                mlResult.className = "p-4 rounded-md mb-4 bg-error text-on-error";
                
                if (e.name === 'AbortError') {
                    mlResult.innerHTML = "Server band (Timeout). Iltimos, keyinroq qayta urinib ko'ring yoki qisqaroq matn kiriting.";
                } else {
                    mlResult.innerHTML = "Xato: " + e.message;
                }
                
                verifyResult.innerHTML = "";
                btn.disabled = false;
                btn.classList.remove('opacity-50', 'cursor-not-allowed');
                btn.innerHTML = originalBtnHTML;
            }
        });
    }
});
