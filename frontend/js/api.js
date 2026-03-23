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

            try {
                const predRes = await fetch("http://localhost:8000/api/predict", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({text: text})
                });
                
                if (predRes.ok) {
                    const predData = await predRes.json();
                    
                    let found = false;
                    let sources = [];

                    // Only attempt verification if input is actual news content
                    if (predData.prediction !== "NOT_NEWS") {
                        const verRes = await fetch("http://localhost:8000/api/verify", {
                            method: "POST",
                            headers: {"Content-Type": "application/json"},
                            body: JSON.stringify({text: predData.text})
                        });
                        
                        if (verRes.ok) {
                            const verData = await verRes.json();
                            found = verData.found;
                            sources = verData.sources;
                        }
                    }
                    
                    // Save result for the next page to read
                    // Source verification overrides ML if trusted sources are found
                    let finalPrediction = predData.prediction;
                    let finalConfidence = predData.confidence;

                    if (found && sources.length > 0 && finalPrediction === "FAKE") {
                        // Trusted sources found — override the ML verdict
                        finalPrediction = "REAL";
                        finalConfidence = 0.90; // High confidence since verified by sources
                    }

                    sessionStorage.setItem('veracity_result', JSON.stringify({
                        prediction: finalPrediction,
                        confidence: finalConfidence,
                        text: text || predData.text,
                        found: found,
                        sources: sources,
                        linguistics: predData.linguistics
                    }));

                    // Redirect to the Analysis Results page
                    window.location.href = 'analysis_results.html';
                } else {
                    const err = await predRes.json();
                    resultsContainer.classList.remove('hidden');
                    mlResult.className = "p-4 rounded-md mb-4 bg-error text-on-error";
                    mlResult.innerHTML = "Xato: " + (err.detail || "Noma'lum xato");
                    verifyResult.innerHTML = "";
                    
                    btn.disabled = false;
                    btn.classList.remove('opacity-50', 'cursor-not-allowed');
                    btn.innerHTML = originalBtnHTML;
                }
            } catch (e) {
                resultsContainer.classList.remove('hidden');
                mlResult.className = "p-4 rounded-md mb-4 bg-error text-on-error";
                mlResult.innerHTML = "Serverga ulanib bo'lmadi. Iltimos, qayta urinib ko'ring.";
                verifyResult.innerHTML = "";
                
                btn.disabled = false;
                btn.classList.remove('opacity-50', 'cursor-not-allowed');
                btn.innerHTML = originalBtnHTML;
            }
        });
    }
});
