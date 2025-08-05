CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
);

DROP TABLE IF EXISTS guests;

CREATE TABLE guests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    drinks TEXT,
    wine_color TEXT,
    wine_type TEXT,
    zags TEXT,
    food TEXT,                 -- аллергии и пожелания
    main_dish TEXT,
    side_dish TEXT,            -- новый гарнир
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);