# seedusers.py
import os, sqlite3, csv, secrets, string, re
from werkzeug.security import generate_password_hash

DB_PATH = "wedding.db"
SCHEMA = "schema.sql"
DOMAIN = "wedding.ru"  # << домен

# ----- Твой список по умолчанию (можно править/дополнять) -----
DEFAULT_NAMES = [
    "Трофимова Татьяна",
    "Трофимов Олег",
    "Владик",
    "Моисеева Марина",
    "Моисеев Олег",
    "Бабушка Тома",
    "Соловьева Елена",
    "Соловьев Олег",
    "Родчихина Кристина",
    "Родчихин Сергей",
    "Трофимова Надежда",
    "Евгений Евгеньевич",
    "Соловьева Татьяна",
    "Трофимов Александр",
    "Трофимова Лидия",
    "Трофимов Андрей",
    "Атлас Елена",
    "Атлас Игорь",
    "Ренат",
    "Регина",
    "Юрики",
    "Юрики (бейби)",
    "Гончарова Маша",
    "Парфенова Светлана",
    "Васютина Таисия",
    "Атлас Маша",
    "Пунга Александра",
    "Даниленко Виктор",
    "Ерж Егор",
    "Никита",
    "Ковалев Дмитрий",
    "Колядин Александр",
    "Денисов Егор",
    "Верёвкин Алексей",
    "Харитонов Кирилл",
]

# ----- Утилиты -----
def ensure_db():
    """Создаёт БД по schema.sql, если файла нет."""
    if not os.path.exists(DB_PATH):
        with sqlite3.connect(DB_PATH) as conn, open(SCHEMA, "r", encoding="utf-8") as f:
            conn.executescript(f.read())

def gen_password(n=8):
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(n))

# простая транслитерация ru->lat (без цифр)
RU2LAT = {
    "а":"a","б":"b","в":"v","г":"g","д":"d","е":"e","ё":"e","ж":"zh","з":"z","и":"i",
    "й":"y","к":"k","л":"l","м":"m","н":"n","о":"o","п":"p","р":"r","с":"s","т":"t",
    "у":"u","ф":"f","х":"h","ц":"c","ч":"ch","ш":"sh","щ":"shch","ъ":"","ы":"y",
    "ь":"","э":"e","ю":"yu","я":"ya",
}
def translit_ru(s: str) -> str:
    out = []
    for ch in s.lower():
        if ch in RU2LAT:
            out.append(RU2LAT[ch])
        elif "a" <= ch <= "z":
            out.append(ch)
        elif ch in " -._":
            out.append(".")
        # прочие символы игнорируем
    res = "".join(out)
    res = re.sub(r"\.+", ".", res).strip(".")
    res = re.sub(r"[^a-z\.]+", "", res)
    return res or "guest"

def unique_local(local: str, used: set[str]) -> str:
    """Возвращает уникальный локал (без цифр)."""
    base = local or "guest"
    candidate = base
    while candidate in used:
        suffix = "-" + "".join(secrets.choice(string.ascii_lowercase) for _ in range(2))
        candidate = base + suffix
    used.add(candidate)
    return candidate

def load_names() -> list[str]:
    """Если есть guests.txt — читаем имена из него (по строке),
       иначе используем DEFAULT_NAMES."""
    if os.path.exists("guests.txt"):
        with open("guests.txt", "r", encoding="utf-8") as f:
            names = [ln.strip() for ln in f if ln.strip()]
        if names:
            return names
    return DEFAULT_NAMES

# ----- Основной сид -----
def seed_from_names(names: list[str]):
    ensure_db()
    created = []

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              email TEXT UNIQUE NOT NULL,
              password_hash TEXT NOT NULL
            );
        """)
        conn.commit()

        used_locals = set()
        # уже занятые локалы из БД (для устойчивости)
        cur.execute("SELECT email FROM users")
        for (email,) in cur.fetchall():
            local = email.split("@", 1)[0]
            used_locals.add(local)

        for name in names:
            local_raw = translit_ru(name)
            local = unique_local(local_raw, used_locals)   # без цифр
            email = f"{local}@{DOMAIN}"
            password = gen_password(8)

            try:
                cur.execute(
                    "INSERT INTO users(email, password_hash) VALUES (?, ?)",
                    (email, generate_password_hash(password)),
                )
                created.append((name, email, password))
            except sqlite3.IntegrityError:
                # если коллизия по email — пропустим
                pass

        conn.commit()

    # выгружаем табличку
    if created:
        out_csv = "users_credentials.csv"
        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["name", "email", "password"])
            w.writerows(created)
        print(f"Создано пользователей: {len(created)}")
        print(f"Файл с логинами/паролями: {out_csv}")
    else:
        print("Новых пользователей не создано.")

if __name__ == "__main__":
    seed_from_names(load_names())
