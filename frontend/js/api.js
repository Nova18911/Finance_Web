const API = '/api';

async function apiGet(path) {
    const r = await fetch(`${API}${path}`);
    if (!r.ok) throw new Error(await r.text() || r.statusText);
    return r.json();
}

async function apiPost(path, body) {
    const r = await fetch(`${API}${path}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });
    if (!r.ok) {
        const t = await r.text();
        throw new Error(t || 'Ошибка запроса');
    }
    if (r.status === 204) return null;
    return r.json().catch(() => null);
}

async function apiPut(path, body) {
    const r = await fetch(`${API}${path}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });
    if (!r.ok) {
        const t = await r.text();
        throw new Error(t || 'Ошибка запроса');
    }
    if (r.status === 204) return null;
    return r.json().catch(() => null);
}

async function apiDelete(path) {
    const r = await fetch(`${API}${path}`, { method: 'DELETE' });
    if (!r.ok) {
        const t = await r.text();
        throw new Error(t || 'Ошибка удаления');
    }
}

function formatMoney(v) {
    return Number(v).toLocaleString('ru-RU', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }) + ' ₽';
}

function formatDate(d) {
    return new Date(d + 'T00:00:00').toLocaleDateString('ru-RU', {
        day: 'numeric',
        month: 'long',
        year: 'numeric'
    });
}

function showMsg(el, ok, text) {
    if (!el) return;
    el.className = ok ? 'alert alert-ok' : 'alert alert-error';
    el.textContent = text;
    el.style.display = 'block';
    setTimeout(() => { el.style.display = 'none'; }, 3500);
}

// стикеры по ТЗ
function stickerClass(total) {
    if (total < 500) return 'sticker-green';
    if (total <= 2000) return 'sticker-yellow';
    return 'sticker-red';
}

function stickerIcon(total) {
    if (total < 500) return '🟢';
    if (total <= 2000) return '🟡';
    return '🔴';
}