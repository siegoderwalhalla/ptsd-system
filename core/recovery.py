"""
RECOVERY — восстановление на Python.
Запуск: python core/recovery.py
"""
import time
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "ptsd.db")

def save_state(state, comment):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO states (timestamp, state, delta) VALUES (?, ?, ?)", (now, int(state), 'none'))
    c.execute("INSERT INTO triggers_log (timestamp, state, code, comment) VALUES (?, ?, ?, ?)", (now, int(state), 'RECOVERY', comment))
    conn.commit()
    conn.close()

def recovery():
    print("🔄 RECOVERY MODE")
    print("=" * 40)
    print()
    print("🌬 Дыхание: вдох 4 сек → выдох 6 сек")
    print("   Выполни 6 циклов:")
    for i in range(1, 7):
        print(f"   Цикл {i}/6 → Вдох...")
        time.sleep(4)
        print("   Выдох...")
        time.sleep(6)

    print()
    state = input("📊 Оцени состояние сейчас (0-10): ")
    comment = input("✍️  Опиши ощущения: ")

    save_state(state, comment)
    print()
    print("✅ Recovery завершён. Запись сохранена.")

if __name__ == "__main__":
    recovery()
