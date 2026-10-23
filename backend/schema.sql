CREATE TABLE IF NOT EXISTS categories (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL UNIQUE,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS expense_items (
    id           SERIAL PRIMARY KEY,
    name         VARCHAR(100) NOT NULL,
    category_id  INTEGER NOT NULL
        REFERENCES categories(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    is_active    BOOLEAN NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_expense_item_name_category UNIQUE (name, category_id)
);

CREATE INDEX IF NOT EXISTS ix_expense_items_category_id
    ON expense_items (category_id);

CREATE INDEX IF NOT EXISTS ix_expense_items_is_active
    ON expense_items (is_active);

CREATE TABLE IF NOT EXISTS transactions (
    id               SERIAL PRIMARY KEY,
    date             DATE NOT NULL,
    amount           NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
    expense_item_id  INTEGER NOT NULL
        REFERENCES expense_items(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    comment          VARCHAR(255) NULL,
    created_at       TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_transactions_date
    ON transactions (date);

CREATE INDEX IF NOT EXISTS ix_transactions_expense_item_id
    ON transactions (expense_item_id);

CREATE INDEX IF NOT EXISTS ix_transactions_date_item
    ON transactions (date, expense_item_id);