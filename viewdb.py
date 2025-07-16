import sqlite3

conn = sqlite3.connect('wedding.db')
cursor = conn.cursor()

print("👤 Пользователи:")
for row in cursor.execute("SELECT id, email FROM users"):
    print(row)

print("\n📋 Ответы гостей:")
for row in cursor.execute("SELECT * FROM guests"):
    print(row)

conn.close()
