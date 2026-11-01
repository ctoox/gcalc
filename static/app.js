document.addEventListener('DOMContentLoaded', () => {
    const stars = document.querySelector('.stars');
    if (stars) {
        for (let i = 0; i < 200; i++) {
            const star = document.createElement('div');
            star.style.cssText = `
                position: absolute;
                width: ${Math.random() * 3}px;
                height: ${Math.random() * 3}px;
                background: #fff;
                border-radius: 50%;
                top: ${Math.random() * 100}%;
                left: ${Math.random() * 100}%;
                opacity: ${Math.random() * 0.8 + 0.2};
                animation: twinkle ${Math.random() * 3 + 2}s infinite;
            `;
            stars.appendChild(star);
        }
    }

    const matchForm = document.getElementById('match-form');
    if (matchForm) {
        matchForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const fd = new FormData(matchForm);
            const data = Object.fromEntries(fd);
            try {
                const resp = await fetch('/api/marriage_match', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                const result = await resp.json();
                const panel = document.getElementById('match-result');
                panel.classList.remove('hidden');
                panel.innerHTML = `<h3>匹配结果</h3><p>分数: ${result.score}</p><p>评价: ${result.verdict}</p>`;
            } catch (err) {
                console.error('Match error:', err);
            }
        });
    }

    const searchBtn = document.getElementById('search-btn');
    if (searchBtn) {
        searchBtn.addEventListener('click', async () => {
            const q = document.getElementById('search-input').value;
            try {
                const resp = await fetch(`/api/persons?q=${encodeURIComponent(q)}`);
                const data = await resp.json();
                const list = document.getElementById('person-list');
                list.innerHTML = data.persons.map(p => `<div class="card">${p.name}</div>`).join('');
            } catch (err) {
                console.error('Search error:', err);
            }
        });
    }
});
