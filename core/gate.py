"""
GATE — шлюз безопасности на Python.
Запуск: python core/gate.py
"""
import sqlite3
import os
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "ptsd.db"

def check_gate():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT state, delta, timestamp FROM states ORDER BY timestamp DESC LIMIT 1")
    row = c.fetchone()

    if not row:
        print("❌ Нет данных. Запишите состояние.")
        conn.close()
        return

    state, delta, ts = row

    # Проверяем наличие триггеров за последние 24 часа
    c.execute("""
        SELECT COUNT(*) FROM triggers_log
        WHERE timestamp > datetime('now', '-1 day') AND code != '_'
    """)
    triggers_recent = c.fetchone()[0]

    print("🚪 PTSD GATE")
    print("=" * 40)
    print(f"   Состояние: {state}/10")
    print(f"   Дельта: {'активна' if delta == 'delta' else 'нет'}")
    print(f"   Триггеров за 24ч: {triggers_recent}")
    print()

    block = 0
    reason = ""

    if state <= 2:
        block = 1
        reason = "КРИТИЧЕСКОЕ СОСТОЯНИЕ — избегайте контактов"
    elif state <= 3:
        block = 1
        reason = "ТЯЖЁЛОЕ СОСТОЯНИЕ — отдохните"
    elif delta == 'delta' and state <= 5:
        block = 1
        reason = "ДЕЛЬТА АКТИВНА — риск срыва"
    elif triggers_recent >= 3:
        block = 1
        reason = "МНОГО ТРИГГЕРОВ — пауза"
    elif state <= 4:
        block = 2
        reason = "ПОНИЖЕННОЕ СОСТОЯНИЕ — осторожно"
    elif state <= 5:
        block = 2
        reason = "СРЕДНЕЕ СОСТОЯНИЕ — берегите себя"

    if block == 1:
        print(f"⛔ ДОСТУП ЗАБЛОКИРОВАН")
        print(f"   {reason}")
        print()
        print("   Что делать: recovery, отдых, забота о себе")
    elif block == 2:
        print(f"⚠️  ОГРАНИЧЕННЫЙ ДОСТУП")
        print(f"   {reason}")
        print()
        print("   Рекомендация: избегайте стрессовых ситуаций")
    else:
        print("✅ ДОСТУП РАЗРЕШЁН")
        print("   Состояние стабильное.")

    conn.close()

if __name__ == "__main__":
    check_gate()
