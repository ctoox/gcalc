document.addEventListener('DOMContentLoaded', () => {
    const fortuneBtn = document.getElementById('fortune-btn');
    if (!fortuneBtn) return;

    fortuneBtn.addEventListener('click', async () => {
        const panel = document.getElementById('fortune-result');
        panel.classList.remove('hidden');
        panel.innerHTML = '<p>加载中...</p>';

        try {
            const resp = await fetch('/api/fortune/daily');
            const data = await resp.json();
            panel.innerHTML = `
                <h3>今日运势</h3>
                <p>日期: ${data.date}</p>
                <p>总体: ${data.overall}</p>
                <p>幸运色: ${data.lucky_color}</p>
                <p>幸运数字: ${data.lucky_number}</p>
            `;
        } catch (err) {
            panel.innerHTML = `<p class="error">获取失败: ${err.message}</p>`;
        }
    });
});
