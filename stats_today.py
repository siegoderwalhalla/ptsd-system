#!/usr/bin/env python3
"""
Python-дайджест: аналитика по army_system_py (чистый Python + sqlite3).
День 44 до дембеля.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.expanduser("~/army_system_py/army.db")

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Общая статистика
    c.execute("SELECT COUNT(*), ROUND(AVG(state), 2), MIN(state), MAX(state) FROM states")
    total, avg, min_s, max_s = c.fetchone()

    # Замеры сегодня
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("SELECT COUNT(*) FROM states WHERE DATE(timestamp) = ?", (today,))
    today_count = c.fetchone()[0]

    # Последний замер
    c.execute("SELECT timestamp, state, delta FROM states ORDER BY timestamp DESC LIMIT 1")
    last = c.fetchone()

    # Вывод
    print("=" * 40)
    print("🛡️  ARMY SYSTEM — PYTHON-ДАЙДЖЕСТ")
    print("=" * 40)
    print(f"   Замеров всего: {total}")
    print(f"   Среднее: {avg}")
    print(f"   Диапазон: {min_s} – {max_s}")
    print(f"   Сегодня: {today_count} замеров")
    if last:
        print(f"   Последний: {last[0]} | {last[1]}/10 | Δ: {last[2]}")
    print("=" * 40)

    conn.close()

if __name__ == "__main__":
    main()
