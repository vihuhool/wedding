# seedusers.py
import os, sqlite3, csv, secrets, string

DB_PATH = "wedding.db"
SCHEMA  = "schema.sql"
DOMAIN  = "wedding.ru"
COUNT   = 40

# базовые наборы для слогов (CV)
CONS = list("pbmnlkrstzvfhdg")   # мягкие/звонкие, звучат «игриво»
VOWS = list("aeiou")             # классические гласные

# фаворитные слоги — будем чаще подмешивать, чтобы чаще выходили pazizu/labubu/pipipo-подобные
FAV = ["pa","pi","po","pu","la","lu","li","bu","ba","zi","zu","zo","mi","mo"]

def ensure_db():
    if not os.path.exists(DB_PATH) and os.path.exists(SCHEMA):
        with sqlite3.connect(DB_PATH) as conn, open(SCHEMA, "r", encoding="utf-8") as f:
            conn.executescript(f.read())

def gen_password(n=8):
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(n))

def rand_syllable() -> str:
    """Один слог CV; фавориты имеют больший шанс."""
    if secrets.randbelow(3) == 0:          # ~33% — взять фаворит
        return secrets.choice(FAV)
    return secrets.choice(CONS) + secrets.choice(VOWS)

def gen_funny_local() -> str:
    """
    Генерируем «смешной» логин без цифр/дефисов.
    Паттерны:
      - [a, b, c]      → pazizu
      - [a, b, b]      → labubu
      - [a, a, b]      → pipipo
      - [a, b, a, b]   → papipa / lazila и т.п.
    """
    a = rand_syllable()
    b = rand_syllable()
    c = rand_syllable()

    pattern = secrets.choice([
        [a, b, c],
        [a, b, b],
        [a, a, b],
        [a, b, a, b],
    ])
    local = "".join(pattern)

    # иногда удлиним ещё одним слогом (редко), но всё равно без дефисов
    if secrets.randbelow(6) == 0:  # ~16%
        local += rand_syllable()
    return local

def unique_local(used: set[str]) -> str:
    for _ in range(60):
        cand = gen_funny_local()
        if cand not in used:
            used.add(cand)
            return cand
    # если совсем невезёт — добавим ещё слог к базе
    base = gen_funny_local()
    while True:
        cand = base + rand_syllable()
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

        # уже занятые локалы
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
                continue

        conn.commit()

    out_csv = "users_credentials.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["email", "password"])
        w.writerows(created)

    print(f"Создано пользователей: {len(created)}")
    print(f"Логины/пароли сохранены в {out_csv}")

if __name__ == "__main__":
    seed_users()
