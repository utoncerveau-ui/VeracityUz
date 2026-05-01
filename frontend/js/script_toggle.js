// Global Script Toggle for Latin <-> Cyrillic Uzbek
document.addEventListener("DOMContentLoaded", () => {
    const scriptToggle = document.getElementById('scriptToggle');
    const latinOpt = document.getElementById('latinOpt');
    const cyrillOpt = document.getElementById('cyrillOpt');
    
    if (scriptToggle) {
        // Load preference
        const savedScript = localStorage.getItem('uz_script') || 'lat';
        setScript(savedScript === 'cyr');

        scriptToggle.addEventListener('click', () => {
            const isCyrillic = cyrillOpt.classList.contains('bg-primary');
            setScript(!isCyrillic);
        });
    }

    function setScript(toCyrillic) {
        if (toCyrillic) {
            latinOpt?.classList.remove('bg-primary', 'text-white');
            latinOpt?.classList.add('text-secondary');
            cyrillOpt?.classList.add('bg-primary', 'text-white');
            cyrillOpt?.classList.remove('text-secondary');
            localStorage.setItem('uz_script', 'cyr');
        } else {
            cyrillOpt?.classList.remove('bg-primary', 'text-white');
            cyrillOpt?.classList.add('text-secondary');
            latinOpt?.classList.add('bg-primary', 'text-white');
            latinOpt?.classList.remove('text-secondary');
            localStorage.setItem('uz_script', 'lat');
        }
        transliterateUI(toCyrillic);
    }

    function transliterateUI(toCyrillic) {
        const map = {
            "Asosiy": "Асосий",
            "Tahlil": "Таҳлил",
            "Algoritm": "Алгоритм",
            "Haqiqatni aniqlang": "Ҳақиқатни аниқланг",
            "Matn tahlili": "Матн таҳлили",
            "Havola orqali": "Ҳавола орқали",
            "Maqola matni": "Мақола матни",
            "Maqola havolasi (URL)": "Мақола ҳаволаси (URL)",
            "Haqiqiyligini tekshirish": "Ҳақиқийлигини текшириш",
            "Qanday ishlaydi?": "Қандай ишлайди?",
            "Maxfiylik": "Махфийлик",
            "So'ngi Tekshiruvlar": "Сўнги Текширувлар",
            "Hammasini ko'rish": "Ҳаммасини кўриш",
            "Tahlil vositalari": "Таҳлил воситалари",
            "Natijalar": "Натижалар",
            "Haqiqiy Ma'lumot": "Ҳақиқий Маълумот",
            "Yolg'on Xabar": "Ёлғон Хабар",
            "Tasdiqlanmagan": "Тасдиқланмаган",
            "Yangilik Emas": "Янгилик Эмас",
            "Tahlil qilinmoqda...": "Таҳлил қилинмоқда...",
            "Ishonch": "Ишонч",
            "Asl matn tahlili": "Асл матн таҳлили",
            "Natijani nusxalash": "Натижани нусхалаш",
            "Orqaga qaytish": "Орқақа қайтиш",
            "Tasdiqlangan Manbalar": "Тасдиқланган Манбалар",
            "Linguistik tahlil": "Лингвистик таҳлил"
        };
        const revMap = Object.fromEntries(Object.entries(map).map(([k, v]) => [v, k]));
        
        document.querySelectorAll('h1, h2, h3, h4, span, button, a, label').forEach(el => {
            const txt = el.innerText.trim();
            if (toCyrillic && map[txt]) el.innerText = map[txt];
            else if (!toCyrillic && revMap[txt]) el.innerText = revMap[txt];
        });
    }
});
