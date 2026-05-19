"""
Экспортёр: выгружает данные из SQLite в CSV/JSON/Markdown.
Запуск: python ~/army_system_py/core/exporter.py [csv|json|md]
"""
import sqlite3
import csv
import json
import os
import sys

DB_PATH = os.path.expanduser("~/army_system_py/army.db")
EXPORT_DIR = os.path.expanduser("~/army_system_py/exports")
os.makedirs(EXPORT_DIR, exist_ok=True)

def export_csv():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT timestamp, state, delta FROM states ORDER BY timestamp")
    rows = c.fetchall()
    path = os.path.join(EXPORT_DIR, "states_export.csv")
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "state", "delta"])
        writer.writerows(rows)
    conn.close()
    print(f"✅ CSV: {path} ({len(rows)} записей)")

def export_json():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT timestamp, state, delta FROM states ORDER BY timestamp")
    rows = c.fetchall()
    data = [{"timestamp": r[0], "state": r[1], "delta": r[2]} for r in rows]
    path = os.path.join(EXPORT_DIR, "states_export.json")
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    conn.close()
    print(f"✅ JSON: {path} ({len(data)} записей)")

def export_markdown():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    path = os.path.join(EXPORT_DIR, "army_report.md")

    c.execute("SELECT COUNT(*), ROUND(AVG(state), 2), MIN(state), MAX(state) FROM states")
    total, avg, min_s, max_s = c.fetchone()

    c.execute("""
        SELECT date, avg_state, min_state, max_state, trigger_count, dominant_trigger
        FROM daily_summary ORDER BY date DESC LIMIT 14
    """)
    daily = c.fetchall()

    c.execute("""
        SELECT code, COUNT(*) as cnt, ROUND(AVG(state), 2)
        FROM triggers_log WHERE code != '_'
        GROUP BY code ORDER BY cnt DESC
    """)
    triggers = c.fetchall()

    with open(path, 'w') as f:
        f.write("# 🛡️ ARMY SYSTEM — Отчёт\n\n")
        f.write(f"*Сгенерировано автоматически*\n\n")
        f.write(f"## 📊 Общая статистика\n\n")
        f.write(f"- Замеров: **{total}**\n")
        f.write(f"- Среднее состояние: **{avg}**\n")
        f.write(f"- Диапазон: **{min_s} – {max_s}**\n\n")

        f.write("## 📅 Последние 14 дней\n\n")
        f.write("| Дата | Среднее | Мин | Макс | Триггеров | Доминантный |\n")
        f.write("|------|---------|-----|------|-----------|-------------|\n")
        for d in daily:
            f.write(f"| {d[0]} | {d[1]} | {d[2]} | {d[3]} | {d[4]} | {d[5]} |\n")

        f.write("\n## 🎯 Триггеры\n\n")
        f.write("| Код | Количество | Среднее состояние |\n")
        f.write("|-----|------------|------------------|\n")
        for t in triggers:
            f.write(f"| {t[0]} | {t[1]} | {t[2]} |\n")

        f.write(f"\n---\n*Создано в Termux, на POCO C51, в армии.*\n")

    conn.close()
    print(f"✅ Markdown: {path}")

if __name__ == "__main__":
    fmt = sys.argv[1] if len(sys.argv) > 1 else "md"
    if fmt == "csv":
        export_csv()
    elif fmt == "json":
        export_json()
    else:
        export_markdown()
