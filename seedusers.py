import os, sqlite3, csv, secrets, string
from werkzeug.security import generate_password_hash

DB_PATH = "wedding.db"
SCHEMA = "schema.sql"

def ensure_db():
    """Создаёт БД по schema.sql, если файла нет."""
    if not os.path.exists(DB_PATH):
        with sqlite3.connect(DB_PATH) as conn, open(SCHEMA, "r", encoding="utf-8") as f:
            conn.executescript(f.read())

def gen_password(n=8):
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(n))

def seed_users(count=40, domain="invite.vihuhool.ru"):
    ensure_db()
    created = []

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        # На всякий — убеждаемся, что таблица есть
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users(
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              email TEXT UNIQUE NOT NULL,
              password_hash TEXT NOT NULL
            );
        """)
        conn.commit()

        for i in range(1, count + 1):
            email = f"guest{i:03d}@{domain}"
            password = gen_password(8)  # короткий: 8 символов
            try:
                cur.execute(
                    "INSERT INTO users(email, password_hash) VALUES (?, ?)",
                    (email, generate_password_hash(password)),
                )
                created.append((email, password))
            except sqlite3.IntegrityError:
                # такой email уже есть — пропускаем
                pass

        conn.commit()

    if created:
        out_csv = "users_credentials.csv"
        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["email", "password"])
            w.writerows(created)
        print(f"Создано пользователей: {len(created)}")
        print(f"Логины/пароли сохранены в {out_csv}")
    else:
        print("Новых пользователей не создано (возможно, уже засеяно ранее).")

if __name__ == "__main__":
    seed_users()