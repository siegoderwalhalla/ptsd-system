"""
PANIC — антипанический протокол на Python.
Запуск: python ~/army_system_py/core/panic.py
"""
import time
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.expanduser("~/army_system_py/army.db")
PLUGINS_DIR = os.path.expanduser("~/army_system_py/plugins")

def save_state(state, comment):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO states (timestamp, state, delta) VALUES (?, ?, ?)", (now, int(state), 'none'))
    c.execute("INSERT INTO triggers_log (timestamp, state, code, comment) VALUES (?, ?, ?, ?)", (now, int(state), 'PANIC', comment))
    conn.commit()
    conn.close()

def panic():
    print("🚨 PANIC MODE")
    print("=" * 40)
    print()
    print("Выполни grounding (5-4-3-2-1):")
    print()

    input("5 вещей, которые ты видишь (нажми Enter когда назвал): ")
    input("4 ощущения в теле (нажми Enter): ")
    input("3 звука (нажми Enter): ")

    print()
    print("🌬 Дыхание: вдох 4 сек → задержка 4 сек → выдох 6 сек")
    print("   Выполни 5 циклов:")
    for i in range(1, 6):
        print(f"   Цикл {i}/5 → Вдох...")
        time.sleep(4)
        print("   Задержка...")
        time.sleep(4)
        print("   Выдох...")
        time.sleep(6)

    print()
    state = input("📊 Оцени состояние сейчас (0-10): ")
    comment = input("✍️  Опиши, что чувствуешь: ")

    save_state(state, comment)
    print()
    print("✅ PANIC завершён. Запись сохранена.")

if __name__ == "__main__":
    panic()
