"""
Анализатор паттернов: находит закономерности в данных PTSD.
Запуск: python core/analyzer.py
"""
import sqlite3
import os
from collections import Counter

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "ptsd.db")

def analyze_patterns():
    """Алиас для analyze()"""
    analyze()

def analyze():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    print("🛡️ АНАЛИЗАТОР ПАТТЕРНОВ")
    print("=" * 50)

    # 1. Общая статистика
    c.execute("SELECT COUNT(*), ROUND(AVG(state), 2), MIN(state), MAX(state) FROM states")
    total, avg, min_s, max_s = c.fetchone()
    print(f"\n📊 ОБЩАЯ СТАТИСТИКА")
    print(f"   Замеров: {total}")
    print(f"   Среднее: {avg}")
    print(f"   Диапазон: {min_s} – {max_s}")

    # 2. Распределение по уровням
    print(f"\n📈 РАСПРЕДЕЛЕНИЕ ПО УРОВНЯМ")
    levels = [
        ("γ⁺ (пиздец)", "state = 1"),
        ("γ  (тяжёлый)", "state = 2"),
        ("γ⁻ (тяжёлый)", "state = 3"),
        ("β⁺ (ср-тяж)", "state = 4"),
        ("β  (средний)", "state = 5"),
        ("β⁻ (ср-лёгк)", "state = 6"),
        ("α⁺ (почти лёгкий)", "state = 7"),
        ("α  (лёгкий)", "state >= 8"),
    ]
    for name, cond in levels:
        c.execute(f"SELECT COUNT(*) FROM states WHERE {cond}")
        count = c.fetchone()[0]
        pct = round(count / total * 100, 1) if total > 0 else 0
        bar = "#" * (int(pct) // 2)
        print(f"   {name:20} {count:3} ({pct:5.1f}%) {bar}")

    # 3. По дням недели
    print(f"\n📅 ПО ДНЯМ НЕДЕЛИ")
    days_ru = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    c.execute("""
        SELECT CAST(strftime('%w', timestamp) AS INTEGER) as dow,
               COUNT(*),
               ROUND(AVG(state), 2)
        FROM states
        WHERE timestamp IS NOT NULL AND timestamp != ''
        GROUP BY dow
        ORDER BY AVG(state) ASC
    """)
    for dow, cnt, avg_s in c.fetchall():
        if dow is None:
            continue
        day = days_ru[dow] if dow < 7 else "?"
        bar = "🔴" if avg_s < 4 else ("🟡" if avg_s < 6 else "🟢")
        print(f"   {day}: среднее {avg_s} {bar} ({cnt} замеров)")

    # 4. По часам
    print(f"\n🕐 ПО ЧАСАМ (топ-5 худших)")
    c.execute("""
        SELECT CAST(strftime('%H', timestamp) AS INTEGER) as hour,
               COUNT(*),
               ROUND(AVG(state), 2)
        FROM states
        WHERE timestamp IS NOT NULL AND timestamp != ''
        GROUP BY hour
        ORDER BY AVG(state) ASC
        LIMIT 5
    """)
    for hour, cnt, avg_s in c.fetchall():
        if hour is None:
            continue
        print(f"   {hour:02d}:00 — среднее {avg_s} ({cnt} замеров)")

    # 5. Триггеры
    print(f"\n🎯 ТРИГГЕРЫ")
    c.execute("""
        SELECT code, COUNT(*) as cnt,
               ROUND(AVG(state), 2) as avg_s
        FROM triggers_log
        WHERE code != '_'
        GROUP BY code
        ORDER BY cnt DESC
    """)
    for code, cnt, avg_s in c.fetchall():
        bar = "🔴" if avg_s < 4 else ("🟡" if avg_s < 6 else "🟢")
        print(f"   {code:8} — {cnt:2} раз, среднее состояние {avg_s} {bar}")

    # 6. Тренд по неделям
    print(f"\n📈 ТРЕНД ПО НЕДЕЛЯМ")
    c.execute("""
        SELECT strftime('%Y-W%W', timestamp) as week,
               COUNT(*),
               ROUND(AVG(state), 2)
        FROM states
        WHERE timestamp IS NOT NULL AND timestamp != ''
        GROUP BY week
        ORDER BY week
    """)
    for week, cnt, avg_s in c.fetchall():
        bar = "🔴" if avg_s < 4 else ("🟡" if avg_s < 6 else "🟢")
        print(f"   {week}: среднее {avg_s} {bar} ({cnt} замеров)")

    # 7. Эффективность восстановления
    print(f"\n💪 ЭФФЕКТИВНОСТЬ ВОССТАНОВЛЕНИЯ")
    print("   (среднее время от гамма-состояния до подъёма выше 5)")
    c.execute("""
        SELECT timestamp, state FROM states
        WHERE state <= 3
        ORDER BY timestamp
    """)
    gamma_times = c.fetchall()
    if gamma_times:
        recovery_times = []
        for ts, _ in gamma_times:
            c.execute("""
                SELECT timestamp FROM states
                WHERE timestamp > ? AND state >= 6
                ORDER BY timestamp LIMIT 1
            """, (ts,))
            recovery = c.fetchone()
            if recovery:
                # Вычисляем разницу в часах
                try:
                    from datetime import datetime
                    t1 = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                    t2 = datetime.strptime(recovery[0], "%Y-%m-%d %H:%M:%S")
                    diff_hours = round((t2 - t1).total_seconds() / 3600, 1)
                    if 0 < diff_hours < 72:
                        recovery_times.append(diff_hours)
                except:
                    pass
        if recovery_times:
            avg_recovery = round(sum(recovery_times) / len(recovery_times), 1)
            print(f"   Среднее время: {avg_recovery} ч")
            print(f"   Самое быстрое: {min(recovery_times)} ч")
            print(f"   Самое долгое: {max(recovery_times)} ч")
        else:
            print("   Недостаточно данных для анализа")
    else:
        print("   Гамма-состояний не зафиксировано")

    conn.close()

if __name__ == "__main__":
    analyze()
