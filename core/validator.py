"""
Валидатор: проверяет базу данных на целостность.
Запуск: python core/validator.py
"""
import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "ptsd.db")

def validate():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    print("🔍 ВАЛИДАТОР ДАННЫХ")
    print("=" * 50)
    issues = 0

    # 1. Проверка на некорректные значения
    c.execute("SELECT COUNT(*) FROM states WHERE state < 0 OR state > 10")
    bad_states = c.fetchone()[0]
    if bad_states:
        print(f"❌ Некорректных значений state: {bad_states}")
        issues += bad_states
    else:
        print("✅ Диапазон state: OK")

    # 2. Проверка на дубликаты
    c.execute("""
        SELECT timestamp, COUNT(*) FROM states
        GROUP BY timestamp
        HAVING COUNT(*) > 1
    """)
    dups = c.fetchall()
    if dups:
        print(f"❌ Дубликатов: {len(dups)}")
        for ts, cnt in dups[:5]:
            print(f"   {ts}: {cnt} раз")
        issues += len(dups)
    else:
        print("✅ Дубликатов: нет")

    # 3. Проверка на пропущенные даты
    c.execute("SELECT MIN(DATE(timestamp)), MAX(DATE(timestamp)) FROM states")
    min_date_str, max_date_str = c.fetchone()
    if min_date_str and max_date_str:
        min_date = datetime.strptime(min_date_str, "%Y-%m-%d")
        max_date = datetime.strptime(max_date_str, "%Y-%m-%d")
        missing_days = 0
        current = min_date
        while current <= max_date:
            c.execute("SELECT COUNT(*) FROM states WHERE DATE(timestamp) = ?", (current.strftime("%Y-%m-%d"),))
            if c.fetchone()[0] == 0:
                missing_days += 1
            current += timedelta(days=1)
        if missing_days:
            print(f"⚠️  Дней без замеров: {missing_days}")
        else:
            print(f"✅ Замеры есть за каждый день с {min_date_str} по {max_date_str}")

    # 4. Проверка на записи без timestamp
    c.execute("SELECT COUNT(*) FROM states WHERE timestamp IS NULL OR timestamp = ''")
    no_ts = c.fetchone()[0]
    if no_ts:
        print(f"❌ Записей без timestamp: {no_ts}")
        issues += no_ts
    else:
        print("✅ Все записи с timestamp")

    # 5. Проверка целостности triggers_log
    c.execute("SELECT COUNT(*) FROM triggers_log WHERE code IS NULL OR code = ''")
    no_code = c.fetchone()[0]
    if no_code:
        print(f"⚠️  Триггеров без кода: {no_code}")

    c.execute("SELECT COUNT(*) FROM triggers_log WHERE state < 0 OR state > 10")
    bad_trig = c.fetchone()[0]
    if bad_trig:
        print(f"❌ Некорректных state в triggers_log: {bad_trig}")
        issues += bad_trig

    # 6. Сверка количества
    c.execute("SELECT COUNT(*) FROM states")
    total_states = c.fetchone()[0]
    c.execute("SELECT COUNT(DISTINCT DATE(timestamp)) FROM states")
    total_days = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM triggers_log")
    total_triggers = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM daily_summary")
    total_summaries = c.fetchone()[0]

    print(f"\n📊 СВОДКА:")
    print(f"   Замеров: {total_states}")
    print(f"   Дней с замерами: {total_days}")
    print(f"   Триггеров: {total_triggers}")
    print(f"   Дневных сводок: {total_summaries}")

    if issues == 0:
        print(f"\n✅ База данных в порядке.")
    else:
        print(f"\n⚠️  Найдено проблем: {issues}")

    conn.close()

if __name__ == "__main__":
    validate()
