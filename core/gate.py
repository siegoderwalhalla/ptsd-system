"""
GATE — шлюз безопасности на Python.
Запуск: python ~/army_system_py/core/gate.py
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.expanduser("~/army_system_py/army.db")

def gate():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT state, delta, timestamp FROM states ORDER BY timestamp DESC LIMIT 1")
    row = c.fetchone()

    if not row:
        print("❌ Нет данных. Запусти state.")
        conn.close()
        return

    state, delta, ts = row

    # Проверяем наличие ТОШ за последние 24 часа
    c.execute("""
        SELECT COUNT(*) FROM triggers_log
        WHERE code = 'ТОШ' AND timestamp > datetime('now', '-1 day')
    """)
    tosh_recent = c.fetchone()[0]

    print("🚪 TOSHA GATE")
    print("=" * 40)
    print(f"   Состояние: {state}/10")
    print(f"   Дельта: {'активна' if delta == 'delta' else 'нет'}")
    print(f"   Триггеров ТОШ за 24ч: {tosh_recent}")
    print()

    block = 0
    reason = ""

    if state <= 2:
        block = 1
        reason = "КРИТИЧЕСКОЕ СОСТОЯНИЕ — не пиши"
    elif state <= 3:
        block = 1
        reason = "ТЯЖЁЛОЕ СОСТОЯНИЕ — не пиши"
    elif delta == 'delta' and state <= 5:
        block = 1
        reason = "ДЕЛЬТА АКТИВНА — риск сорваться"
    elif tosh_recent >= 3:
        block = 1
        reason = "МНОГО ТРИГГЕРОВ ТОШ — подожди"
    elif state <= 4:
        block = 2
        reason = "ПОНИЖЕННОЕ СОСТОЯНИЕ — осторожно"
    elif state <= 5:
        block = 2
        reason = "СРЕДНЕЕ СОСТОЯНИЕ — коротко и без претензий"

    if block == 1:
        print(f"⛔ ДОСТУП ЗАБЛОКИРОВАН")
        print(f"   {reason}")
        print()
        print("   Что делать: recovery, не пиши Тошке")
    elif block == 2:
        print(f"⚠️  ОГРАНИЧЕННЫЙ ДОСТУП")
        print(f"   {reason}")
        print()
        print("   Можно: коротко, спросить про неё, без претензий")
    else:
        print("✅ ДОСТУП РАЗРЕШЁН")
        print("   Можно писать.")

    conn.close()

if __name__ == "__main__":
    gate()
