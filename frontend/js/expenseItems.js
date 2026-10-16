const tbody = document.getElementById('item-tbody');
const nameInput = document.getElementById('item-name');
const catSelect = document.getElementById('item-category');
const activeSelect = document.getElementById('item-active');
const addBtn = document.getElementById('item-add');
const msgEl = document.getElementById('item-msg');

let categories = [];

async function loadCategories() {
    categories = await apiGet('/Categories');
    catSelect.innerHTML = '<option disabled selected value="">— выберите —</option>';
    for (const c of categories) {
        const opt = document.createElement('option');
        opt.value = c.id;
        opt.textContent = c.name;
        catSelect.appendChild(opt);
    }
}

async function loadItems() {
    try {
        const list = await apiGet('/ExpenseItems');
        tbody.innerHTML = '';
        if (!list.length) {
            tbody.innerHTML = '<tr><td colspan="4" class="empty">Статей пока нет</td></tr>';
            return;
        }
        for (const it of list) {
            const catName = it.category?.name ?? categories.find(c => c.id === it.categoryId)?.name ?? '—';
            const active = it.isActive;
            const tr = document.createElement('tr');
            tr.innerHTML = `
        <td>${escapeHtml(it.name)}</td>
        <td>${escapeHtml(catName)}</td>
        <td><span class="badge ${active ? 'badge-on' : 'badge-off'}">${active ? 'Активна' : 'Не активна'}</span></td>
        <td style="display:flex;gap:6px;flex-wrap:wrap;">
          <button class="btn btn-ghost btn-sm" type="button" data-edit="${it.id}">✏️ Изм.</button>
          <button class="btn btn-danger btn-sm" type="button" data-del="${it.id}">🗑 Удалить</button>
        </td>
      `;
            tr.dataset.json = JSON.stringify(it);
            tbody.appendChild(tr);
        }
    } catch (e) {
        showMsg(msgEl, false, e.message || 'Не удалось загрузить статьи');
    }
}

addBtn.addEventListener('click', async () => {
    const name = nameInput.value.trim();
    const categoryId = Number(catSelect.value);
    const isActive = activeSelect.value === 'true';
    if (!name) return showMsg(msgEl, false, 'Введите название статьи');
    if (!categoryId) return showMsg(msgEl, false, 'Выберите категорию');
    try {
        await apiPost('/ExpenseItems', { name, categoryId, isActive });
        nameInput.value = '';
        catSelect.value = '';
        activeSelect.value = 'true';
        showMsg(msgEl, true, 'Статья добавлена');
        await loadItems();
    } catch (e) {
        showMsg(msgEl, false, e.message || 'Ошибка при создании');
    }
});

tbody.addEventListener('click', async (e) => {
    const del = e.target.closest('[data-del]');
    const edit = e.target.closest('[data-edit]');

    if (del) {
        if (!confirm('Удалить статью?')) return;
        try {
            await apiDelete(`/ExpenseItems/${del.dataset.del}`);
            showMsg(msgEl, true, 'Статья удалена');
            await loadItems();
        } catch (err) {
            showMsg(msgEl, false, err.message || 'Нельзя удалить статью');
        }
    }

    if (edit) {
        const row = edit.closest('tr');
        const it = JSON.parse(row.dataset.json);
        const newName = prompt('Название:', it.name);
        if (newName === null || !newName.trim()) return;
        const newActive = confirm('Сделать активной? OK = да, Отмена = нет');
        try {
            await apiPut(`/ExpenseItems/${it.id}`, {
                id: it.id,
                name: newName.trim(),
                categoryId: it.categoryId,
                isActive: newActive
            });
            showMsg(msgEl, true, 'Статья сохранена');
            await loadItems();
        } catch (err) {
            showMsg(msgEl, false, err.message || 'Ошибка при сохранении');
        }
    }
});

function escapeHtml(s) {
    return String(s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

(async () => {
    try {
        await loadCategories();
        await loadItems();
    } catch (e) {
        showMsg(msgEl, false, e.message || 'Ошибка загрузки');
    }
})();