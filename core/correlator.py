"""
Коррелятор: ищет связи между параметрами.
Запуск: python ~/army_system_py/core/correlator.py
"""
import sqlite3
import os

DB_PATH = os.path.expanduser("~/army_system_py/army.db")

def correlate():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    print("🔗 КОРРЕЛЯТОР СВЯЗЕЙ")
    print("=" * 50)

    # Корреляция: день недели → среднее состояние
    print("\n📅 ДЕНЬ НЕДЕЛИ → СОСТОЯНИЕ")
    c.execute("""
        SELECT CAST(strftime('%w', timestamp) AS INTEGER) as dow,
               ROUND(AVG(state), 2), COUNT(*)
        FROM states
        GROUP BY dow
        ORDER BY AVG(state) ASC
    """)
    days_ru = ["Вс", "Пн", "Вт", "Ср", "Чт", "Пт", "Сб"]
    for dow, avg_s, cnt in c.fetchall():
        day = days_ru[dow] if dow is not None and dow < 7 else "?"
        print(f"   {day}: среднее {avg_s} ({cnt} замеров)")

    # Корреляция: час суток → среднее состояние
    print("\n🕐 ЧАС СУТОК → СОСТОЯНИЕ")
    c.execute("""
        SELECT CAST(strftime('%H', timestamp) AS INTEGER) as hour,
               ROUND(AVG(state), 2), COUNT(*)
        FROM states
        GROUP BY hour
        ORDER BY AVG(state) ASC
        LIMIT 8
    """)
    for hour, avg_s, cnt in c.fetchall():
        print(f"   {hour:02d}:00 — среднее {avg_s} ({cnt} замеров)")

    # Корреляция: дельта → среднее состояние
    print("\nΔ ДЕЛЬТА → СОСТОЯНИЕ")
    c.execute("""
        SELECT delta, ROUND(AVG(state), 2), COUNT(*)
        FROM states
        GROUP BY delta
    """)
    for delta, avg_s, cnt in c.fetchall():
        label = "Δ активна" if delta == 'delta' else "Δ нет"
        print(f"   {label}: среднее {avg_s} ({cnt} замеров)")

    # Корреляция: триггер → среднее состояние
    print("\n🎯 ТРИГГЕР → СРЕДНЕЕ СОСТОЯНИЕ")
    c.execute("""
        SELECT code, ROUND(AVG(state), 2), COUNT(*)
        FROM triggers_log
        WHERE code != '_'
        GROUP BY code
        HAVING COUNT(*) >= 1
        ORDER BY AVG(state) ASC
    """)
    for code, avg_s, cnt in c.fetchall():
        bar = "🔴" if avg_s < 4 else ("🟡" if avg_s < 6 else "🟢")
        print(f"   {code:8} — среднее {avg_s} {bar} ({cnt} раз)")

    # Корреляция: плотность замеров → среднее
    print("\n📊 ПЛОТНОСТЬ ЗАМЕРОВ → СРЕДНЕЕ")
    c.execute("""
        SELECT DATE(timestamp) as day, COUNT(*), ROUND(AVG(state), 2)
        FROM states
        GROUP BY day
        HAVING COUNT(*) >= 3
        ORDER BY AVG(state) DESC
        LIMIT 5
    """)
    for day, cnt, avg_s in c.fetchall():
        print(f"   {day}: {cnt} замеров, среднее {avg_s}")

    conn.close()

if __name__ == "__main__":
    correlate()
