-- Инициализация БД для варианта "Онлайн-переводчик".
-- Таблица истории переводов + пара примеров для наглядности.

CREATE TABLE IF NOT EXISTS translations (
    id              SERIAL PRIMARY KEY,
    original_text   TEXT NOT NULL,
    translated_text TEXT NOT NULL,
    source_lang     VARCHAR(10) NOT NULL DEFAULT 'auto',
    target_lang     VARCHAR(10) NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- индекс, чтобы последние переводы выбирались быстро
CREATE INDEX IF NOT EXISTS idx_translations_created_at
    ON translations (created_at DESC);

-- немного стартовых данных
INSERT INTO translations (original_text, translated_text, source_lang, target_lang) VALUES
    ('Добрый день!',            'Good afternoon!',         'ru', 'en'),
    ('Как дела?',               'How are you?',            'ru', 'en'),
    ('Спасибо за помощь',       'Thank you for help',      'ru', 'en'),
    ('Good morning',            'Доброе утро',             'en', 'ru'),
    ('Docker Compose is great', 'Docker Compose — отлично','en', 'ru');