"""
Импортёр данных из CSV старой системы в SQLite новой.
Запуск: python core/importer.py
"""
import sqlite3
import csv
import os
from datetime import datetime

# Пути
OLD_LOGS = os.path.expanduser("~/ptsd_monitor/logs")
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "ptsd.db")

def import_data():
    """Универсальная функция импорта"""
    main()

def create_tables(cursor):
    """Создаёт таблицы, если их нет"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS states (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            state INTEGER NOT NULL CHECK(state BETWEEN 0 AND 10),
            delta TEXT DEFAULT 'none',
            trigger_code TEXT DEFAULT '_',
            comment TEXT DEFAULT ''
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_summary (
            date TEXT PRIMARY KEY,
            avg_state REAL,
            min_state INTEGER,
            max_state INTEGER,
            trigger_count INTEGER,
            delta_count INTEGER,
            dominant_trigger TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS triggers_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            state INTEGER,
            code TEXT,
            comment TEXT
        )
    """)

def import_state_raw(conn):
    """Импорт из state_raw.log"""
    raw_file = os.path.join(OLD_LOGS, "state_raw.log")
    if not os.path.exists(raw_file):
        print("❌ state_raw.log не найден")
        return 0

    c = conn.cursor()
    count = 0
    with open(raw_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('-csv') or line.startswith('-log'):
                continue
            parts = line.split(',')
            if len(parts) < 2:
                continue
            timestamp = parts[0].strip()
            state_str = parts[1].strip()
            if not timestamp or not state_str:
                continue
            try:
                state = int(state_str)
                if state < 0 or state > 10:
                    continue
            except ValueError:
                continue
            delta = 'none'
            if len(parts) >= 3 and parts[2].strip() == 'delta':
                delta = 'delta'
            # Нормализация timestamp
            if len(timestamp) == 16:  # YYYY-MM-DD HH:MM
                timestamp += ":00"
            try:
                c.execute(
                    "INSERT INTO states (timestamp, state, delta) VALUES (?, ?, ?)",
                    (timestamp, state, delta)
                )
                count += 1
            except:
                pass
    conn.commit()
    return count

def import_trigger_history(conn):
    """Импорт из trigger_history.csv"""
    trig_file = os.path.join(OLD_LOGS, "trigger_history.csv")
    if not os.path.exists(trig_file):
        print("❌ trigger_history.csv не найден")
        return 0

    c = conn.cursor()
    count = 0
    with open(trig_file, 'r') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if len(row) < 4:
                continue
            timestamp = row[0].strip()
            state_str = row[1].strip()
            code = row[2].strip().strip('"')
            comment = row[3].strip().strip('"')
            if not timestamp or not state_str:
                continue
            try:
                state = int(state_str)
                if state < 0 or state > 10:
                    continue
            except ValueError:
                continue
            if len(timestamp) == 16:
                timestamp += ":00"
            try:
                c.execute(
                    "INSERT INTO triggers_log (timestamp, state, code, comment) VALUES (?, ?, ?, ?)",
                    (timestamp, state, code, comment)
                )
                count += 1
            except:
                pass
    conn.commit()
    return count

def build_daily_summary(conn):
    """Строит сводку по дням"""
    c = conn.cursor()
    c.execute("""
        SELECT DATE(timestamp) as day,
               ROUND(AVG(state), 2),
               MIN(state),
               MAX(state),
               COUNT(*)
        FROM states
        WHERE timestamp IS NOT NULL AND timestamp != ''
        GROUP BY day
        ORDER BY day
    """)
    rows = c.fetchall()
    count = 0
    for day, avg_s, min_s, max_s, total in rows:
        # Триггеры за день
        c.execute("SELECT COUNT(*) FROM triggers_log WHERE DATE(timestamp) = ?", (day,))
        trig_count = c.fetchone()[0]
        # Дельта за день
        c.execute("SELECT COUNT(*) FROM states WHERE DATE(timestamp) = ? AND delta = 'delta'", (day,))
        delta_count = c.fetchone()[0]
        # Доминирующий триггер
        c.execute("""
            SELECT code, COUNT(*) as cnt FROM triggers_log
            WHERE DATE(timestamp) = ? AND code != '_'
            GROUP BY code ORDER BY cnt DESC LIMIT 1
        """, (day,))
        dom = c.fetchone()
        dominant = dom[0] if dom else '-'
        try:
            c.execute(
                "INSERT OR REPLACE INTO daily_summary VALUES (?, ?, ?, ?, ?, ?, ?)",
                (day, avg_s, min_s, max_s, trig_count, delta_count, dominant)
            )
            count += 1
        except:
            pass
    conn.commit()
    return count

def main():
    print("🧠 Импорт данных PTSD Monitor → SQLite")
    print("=" * 40)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    create_tables(c)
    conn.commit()

    n1 = import_state_raw(conn)
    print(f"✅ Состояний импортировано: {n1}")

    n2 = import_trigger_history(conn)
    print(f"✅ Триггеров импортировано: {n2}")

    n3 = build_daily_summary(conn)
    print(f"✅ Дневных сводок создано: {n3}")

    # Статистика
    c.execute("SELECT COUNT(*) FROM states")
    total_states = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM triggers_log")
    total_triggers = c.fetchone()[0]
    c.execute("SELECT ROUND(AVG(state), 2) FROM states")
    avg_state = c.fetchone()[0]

    print(f"\n📊 ИТОГО:")
    print(f"   Замеров: {total_states}")
    print(f"   Триггеров: {total_triggers}")
    print(f"   Среднее состояние: {avg_state}")
    print(f"   База: {DB_PATH}")

    conn.close()

if __name__ == "__main__":
    main()
