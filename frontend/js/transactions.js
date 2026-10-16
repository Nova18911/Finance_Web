const dateInput = document.getElementById('tx-date');
const amountInput = document.getElementById('tx-amount');
const itemSelect = document.getElementById('tx-item');
const commentInput = document.getElementById('tx-comment');
const addBtn = document.getElementById('tx-add');
const msgEl = document.getElementById('tx-msg');
const listEl = document.getElementById('tx-list');
const monthLabel = document.getElementById('tx-month-label');
const prevBtn = document.getElementById('tx-prev');
const nextBtn = document.getElementById('tx-next');

const today = new Date();
let year = today.getFullYear();
let month = today.getMonth() + 1;

dateInput.value = today.toISOString().slice(0, 10);

function updateMonthLabel() {
    const d = new Date(year, month - 1);
    monthLabel.textContent = d.toLocaleString('ru-RU', { month: 'long', year: 'numeric' });
}

async function loadActiveItems() {
    const items = await apiGet('/ExpenseItems');
    itemSelect.innerHTML = '<option disabled selected value="">— выберите —</option>';
    for (const it of items.filter(i => i.isActive)) {
        const opt = document.createElement('option');
        opt.value = it.id;
        opt.textContent = it.name;
        itemSelect.appendChild(opt);
    }
}

async function loadTransactions() {
    try {
        const list = await apiGet(`/Transactions/byMonth/${year}/${month}`);
        listEl.innerHTML = '';

        if (!list.length) {
            listEl.innerHTML = '<div class="empty">Транзакций за этот месяц нет</div>';
            return;
        }

        const map = {};
        for (const tx of list) {
            if (!map[tx.date]) map[tx.date] = { date: tx.date, items: [], total: 0 };
            map[tx.date].items.push(tx);
            map[tx.date].total += Number(tx.amount);
        }

        const days = Object.values(map).sort((a, b) => b.date.localeCompare(a.date));

        for (const day of days) {
            const block = document.createElement('div');
            block.className = 'day-block';
            block.innerHTML = `
        <div class="day-header">
          <span class="day-title">${formatDate(day.date)}</span>
          <span class="sticker ${stickerClass(day.total)}">${stickerIcon(day.total)} ${formatMoney(day.total)}</span>
          <span class="day-total">расходы за день</span>
        </div>
        <div class="card" style="padding:0;overflow:hidden">
          <table>
            <thead>
              <tr>
                <th>Статья</th>
                <th>Сумма</th>
                <th>Комментарий</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              ${day.items.map(tx => `
                <tr>
                  <td>${escapeHtml(tx.expenseItem?.name || '—')}</td>
                  <td style="color:var(--red)">${formatMoney(tx.amount)}</td>
                  <td style="color:var(--muted)">${escapeHtml(tx.comment || '—')}</td>
                  <td><button class="btn btn-danger btn-sm" type="button" data-del="${tx.id}">🗑</button></td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `;
            listEl.appendChild(block);
        }
    } catch (e) {
        showMsg(msgEl, false, e.message || 'Не удалось загрузить транзакции');
    }
}

addBtn.addEventListener('click', async () => {
    const date = dateInput.value;
    const amount = Number(amountInput.value);
    const expenseItemId = Number(itemSelect.value);
    const comment = commentInput.value.trim() || null;

    if (!date) return showMsg(msgEl, false, 'Укажите дату');
    if (!amount || amount <= 0) return showMsg(msgEl, false, 'Укажите сумму');
    if (!expenseItemId) return showMsg(msgEl, false, 'Выберите статью расхода');

    try {
        await apiPost('/Transactions', { date, amount, expenseItemId, comment });
        amountInput.value = '';
        commentInput.value = '';
        itemSelect.value = '';
        showMsg(msgEl, true, 'Транзакция добавлена');
        await loadTransactions();
    } catch (e) {
        showMsg(msgEl, false, e.message || 'Ошибка при создании');
    }
});

listEl.addEventListener('click', async (e) => {
    const del = e.target.closest('[data-del]');
    if (!del) return;
    if (!confirm('Удалить транзакцию?')) return;
    try {
        await apiDelete(`/Transactions/${del.dataset.del}`);
        showMsg(msgEl, true, 'Транзакция удалена');
        await loadTransactions();
    } catch (err) {
        showMsg(msgEl, false, err.message || 'Ошибка удаления');
    }
});

prevBtn.addEventListener('click', () => {
    if (month === 1) { month = 12; year--; }
    else month--;
    updateMonthLabel();
    loadTransactions();
});

nextBtn.addEventListener('click', () => {
    if (month === 12) { month = 1; year++; }
    else month++;
    updateMonthLabel();
    loadTransactions();
});

function escapeHtml(s) {
    return String(s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

(async () => {
    updateMonthLabel();
    try {
        await loadActiveItems();
        await loadTransactions();
    } catch (e) {
        showMsg(msgEl, false, e.message || 'Ошибка загрузки');
    }
})();