# seedusers.py
import os, sqlite3, csv, secrets, string

DB_PATH = "wedding.db"
SCHEMA = "schema.sql"
DOMAIN = "wedding.ru"   # домен для логинов
COUNT  = 40             # сколько учёток создать

# слоги для "читаемых" логинов (без цифр)
SYLL = [
    "ma","me","mi","mo","mu","na","ne","ni","no","nu","la","le","li","lo","lu",
    "ra","re","ri","ro","ru","ta","te","ti","to","tu","ka","ke","ki","ko","ku",
    "sa","se","si","so","su","va","ve","vi","vo","vu","pa","pe","pi","po","pu",
    "ba","be","bi","bo","bu","ga","ge","gi","go","gu","fa","fe","fi","fo","fu",
    "ya","ye","yo","yu","za","ze","zi","zo","zu","xa","xe","xi","xo","xu"
]

def ensure_db():
    """Создать БД по schema.sql, если файла нет."""
    if not os.path.exists(DB_PATH) and os.path.exists(SCHEMA):
        with sqlite3.connect(DB_PATH) as conn, open(SCHEMA, "r", encoding="utf-8") as f:
            conn.executescript(f.read())

def gen_password(n=8):
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(n))

def gen_local():
    """Генерирует логин без цифр: 2–3 слога + опциональный -слог."""
    parts = [secrets.choice(SYLL) for _ in range(secrets.choice([2,3]))]
    local = "".join(parts)
    # иногда добавим -слог для разнообразия
    if secrets.randbelow(3) == 0:
        local += "-" + secrets.choice(SYLL).rstrip("aeiou")  # чуть компактнее
    return local

def unique_local(used: set[str]) -> str:
    """Возвращает уникальный локал (только буквы/дефис)."""
    for _ in range(50):
        cand = gen_local()
        if cand not in used:
            used.add(cand)
            return cand
    # редкий случай большого числа коллизий — добавим буквенный суффикс
    base = gen_local()
    while True:
        cand = base + "-" + "".join(secrets.choice(string.ascii_lowercase) for _ in range(2))
        if cand not in used:
            used.add(cand)
            return cand

def seed_users(count=COUNT, domain=DOMAIN):
    ensure_db()
    created = []

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users(
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              email TEXT UNIQUE NOT NULL,
              password_hash TEXT NOT NULL
            );
        """)
        conn.commit()

        # соберём уже занятые локалы, чтобы не конфликтовать
        used = set()
        cur.execute("SELECT email FROM users")
        for (email,) in cur.fetchall():
            used.add(email.split("@",1)[0])

        from werkzeug.security import generate_password_hash

        while len(created) < count:
            local = unique_local(used)
            email = f"{local}@{domain}"
            pwd   = gen_password(8)

            try:
                cur.execute(
                    "INSERT INTO users(email, password_hash) VALUES (?, ?)",
                    (email, generate_password_hash(pwd)),
                )
                created.append((email, pwd))
            except sqlite3.IntegrityError:
                # крайне маловероятно, но попробуем ещё
                continue

        conn.commit()

    # выгрузим CSV
    out_csv = "users_credentials.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["email", "password"])
        w.writerows(created)

    print(f"Создано пользователей: {len(created)}")
    print(f"Логины/пароли сохранены в {out_csv}")

if __name__ == "__main__":
    seed_users()
