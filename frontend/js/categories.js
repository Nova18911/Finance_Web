const tbody = document.getElementById('cat-tbody');
const nameInput = document.getElementById('cat-name');
const addBtn = document.getElementById('cat-add');
const msgEl = document.getElementById('cat-msg');

async function loadCategories() {
    try {
        const list = await apiGet('/Categories');
        tbody.innerHTML = '';
        if (!list.length) {
            tbody.innerHTML = '<tr><td colspan="2" class="empty">Категорий пока нет</td></tr>';
            return;
        }
        for (const c of list) {
            const tr = document.createElement('tr');
            tr.innerHTML = `
        <td>${escapeHtml(c.name)}</td>
        <td style="display:flex;gap:6px;flex-wrap:wrap;">
          <button class="btn btn-ghost btn-sm" type="button" data-edit="${c.id}">✏️ Изм.</button>
          <button class="btn btn-danger btn-sm" type="button" data-del="${c.id}">🗑 Удалить</button>
        </td>
      `;
            tbody.appendChild(tr);
        }
    } catch (e) {
        showMsg(msgEl, false, e.message || 'Не удалось загрузить категории');
    }
}

addBtn.addEventListener('click', async () => {
    const name = nameInput.value.trim();
    if (!name) return showMsg(msgEl, false, 'Введите название категории');
    try {
        await apiPost('/Categories', { name });
        nameInput.value = '';
        showMsg(msgEl, true, 'Категория добавлена');
        await loadCategories();
    } catch (e) {
        showMsg(msgEl, false, e.message || 'Ошибка при создании');
    }
});

tbody.addEventListener('click', async (e) => {
    const del = e.target.closest('[data-del]');
    const edit = e.target.closest('[data-edit]');

    if (del) {
        if (!confirm('Удалить категорию?')) return;
        try {
            await apiDelete(`/Categories/${del.dataset.del}`);
            showMsg(msgEl, true, 'Категория удалена');
            await loadCategories();
        } catch (err) {
            showMsg(msgEl, false, err.message || 'Нельзя удалить категорию');
        }
    }

    if (edit) {
        const id = edit.dataset.edit;
        const row = edit.closest('tr');
        const currentName = row.cells[0].textContent;
        const newName = prompt('Новое название:', currentName);
        if (newName === null || !newName.trim()) return;
        try {
            await apiPut(`/Categories/${id}`, { id: Number(id), name: newName.trim() });
            showMsg(msgEl, true, 'Категория сохранена');
            await loadCategories();
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

loadCategories();