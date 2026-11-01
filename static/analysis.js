document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('analysis-form');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const fd = new FormData(form);
        const data = {
            year: parseInt(fd.get('year')),
            month: parseInt(fd.get('month')),
            day: parseInt(fd.get('day')),
            hour: parseInt(fd.get('hour'))
        };

        const resultPanel = document.getElementById('result');
        resultPanel.classList.remove('hidden');
        resultPanel.innerHTML = '<p>分析中...</p>';

        try {
            const resp = await fetch('/api/full_analysis', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            });
            const result = await resp.json();
            resultPanel.innerHTML = `
                <h3>分析结果</h3>
                <div class="result-section">
                    <h4>八字</h4>
                    <p>天干: ${result.bazi.gan} 地支: ${result.bazi.zhi}</p>
                </div>
                <div class="result-section">
                    <h4>周易</h4>
                    <p>卦象: ${result.yijing.name} (第${result.yijing.hexagram}卦)</p>
                </div>
                <div class="result-section">
                    <h4>综合评分</h4>
                    <p>${result.score}/100</p>
                </div>
            `;
        } catch (err) {
            resultPanel.innerHTML = `<p class="error">分析失败: ${err.message}</p>`;
        }
    });
});
