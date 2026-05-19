"""
Синхронизатор: добавляет новые записи из CSV в SQLite.
Запуск: python ~/army_system_py/core/sync_bash.py
"""
import sqlite3
import csv
import os

OLD_LOGS = os.path.expanduser("~/army_system/logs")
DB_PATH = os.path.expanduser("~/army_system_py/army.db")

def get_last_timestamp(cursor, table):
    cursor.execute(f"SELECT MAX(timestamp) FROM {table}")
    result = cursor.fetchone()[0]
    return result if result else "1970-01-01 00:00:00"

def sync_states(conn):
    raw_file = os.path.join(OLD_LOGS, "state_raw.log")
    if not os.path.exists(raw_file):
        print("❌ state_raw.log не найден")
        return 0

    c = conn.cursor()
    last_ts = get_last_timestamp(c, "states")
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
            if len(timestamp) == 16:
                timestamp += ":00"
            if timestamp <= last_ts:
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

def sync_triggers(conn):
    trig_file = os.path.join(OLD_LOGS, "trigger_history.csv")
    if not os.path.exists(trig_file):
        print("❌ trigger_history.csv не найден")
        return 0

    c = conn.cursor()
    last_ts = get_last_timestamp(c, "triggers_log")
    count = 0

    with open(trig_file, 'r') as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if len(row) < 4:
                continue
            timestamp = row[0].strip()
            if len(timestamp) == 16:
                timestamp += ":00"
            if timestamp <= last_ts:
                continue
            state_str = row[1].strip()
            code = row[2].strip().strip('"')
            comment = row[3].strip().strip('"')
            try:
                state = int(state_str)
                if state < 0 or state > 10:
                    continue
            except ValueError:
                continue
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

def main():
    conn = sqlite3.connect(DB_PATH)
    print("🔄 Синхронизация bash → SQLite")
    n1 = sync_states(conn)
    n2 = sync_triggers(conn)
    print(f"✅ Новых состояний: {n1}")
    print(f"✅ Новых триггеров: {n2}")
    if n1 == 0 and n2 == 0:
        print("   Всё синхронизировано.")
    conn.close()

if __name__ == "__main__":
    main()
