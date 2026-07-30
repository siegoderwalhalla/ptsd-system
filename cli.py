#!/usr/bin/env python3
"""
PTSD Monitor — CLI клиент для мониторинга психического состояния.
Запуск: python cli.py <command> [args]
Выход: Ctrl+C или команда exit
"""
import sqlite3
import os
import sys
from datetime import datetime, date, timedelta
from pathlib import Path

# Пути
DB_PATH = Path(__file__).parent / "data" / "ptsd.db"
EXPORTS_DIR = Path(__file__).parent / "exports"

# Коды триггеров (обновлённые)
TRIGGER_CODES = {
    "TRIGGER_ABUSE": "Абьюзивное взаимодействие",
    "TRIGGER_CONFLICT": "Конфликт",
    "TRIGGER_LONELY": "Одиночество",
    "TRIGGER_INTRUSIVE": "Навязчивые воспоминания",
    "TRIGGER_DEATH": "Смерть, утрата",
    "TRIGGER_GUILT": "Вина, стыд",
    "TRIGGER_IMPULSE": "Импульсы",
    "TRIGGER_GENERAL": "Общий триггер",
    "THOUGHT": "Мысли о себе",
    "SLEEP": "Проблемы со сном",
    "DREAM": "Триггерные сны",
    "_": "Нет триггера"
}

LEVELS = {
    10: "α⁺⁺ (отлично)",
    9: "α⁺ (хорошо)",
    8: "α (норма+)",
    7: "β⁻ (норма-)",
    6: "β (средне)",
    5: "β⁺ (ниже среднего)",
    4: "γ⁻ (тяжело)",
    3: "γ (очень тяжело)",
    2: "γ⁺ (кризис)",
    1: "γ⁺⁺ (критическое)"
}


def init_db():
    """Инициализация базы данных"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Таблица состояний
    c.execute("""
        CREATE TABLE IF NOT EXISTS states (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            state INTEGER NOT NULL,
            delta TEXT,
            comment TEXT
        )
    """)
    
    # Таблица триггеров
    c.execute("""
        CREATE TABLE IF NOT EXISTS triggers_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            code TEXT NOT NULL,
            state INTEGER,
            comment TEXT
        )
    """)
    
    # Таблица recovery
    c.execute("""
        CREATE TABLE IF NOT EXISTS recovery_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            before_state INTEGER,
            after_state INTEGER,
            technique TEXT,
            comment TEXT
        )
    """)
    
    # Таблица panic
    c.execute("""
        CREATE TABLE IF NOT EXISTS panic_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            before_state INTEGER,
            after_state INTEGER,
            grounding_done TEXT,
            comment TEXT
        )
    """)
    
    conn.commit()
    conn.close()


def get_level(state):
    """Получить уровень состояния"""
    return LEVELS.get(state, f"уровень {state}")


def cmd_state(args):
    """Запись состояния"""
    if not args or len(args) < 1:
        print("❌ Использование: python cli.py state <0-10> [delta] [code] [comment]")
        return
    
    try:
        state = int(args[0])
        if state < 0 or state > 10:
            print("❌ Состояние должно быть от 0 до 10")
            return
    except ValueError:
        print("❌ Состояние должно быть числом")
        return
    
    delta = args[1] if len(args) > 1 and args[1].lower() in ['delta', 'д'] else None
    code = args[2] if len(args) > 2 else "_"
    comment = " ".join(args[3:]) if len(args) > 3 else ""
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Запись состояния
    c.execute(
        "INSERT INTO states (state, delta, comment) VALUES (?, ?, ?)",
        (state, delta, comment)
    )
    
    # Если есть код триггера
    if code and code != "_":
        c.execute(
            "INSERT INTO triggers_log (code, state, comment) VALUES (?, ?, ?)",
            (code, state, comment)
        )
    
    conn.commit()
    conn.close()
    
    level = get_level(state)
    delta_str = " Δ АКТИВНА" if delta else ""
    print(f"✅ Состояние записано: {state}/10 — {level}{delta_str}")
    if code and code != "_":
        trigger_name = TRIGGER_CODES.get(code, code)
        print(f"   Триггер: {trigger_name}")
    if comment:
        print(f"   Комментарий: {comment}")


def cmd_recovery(args):
    """Запись recovery-сессии"""
    if not args or len(args) < 2:
        print("❌ Использование: python cli.py recovery <before> <after> [technique] [comment]")
        return
    
    try:
        before = int(args[0])
        after = int(args[1])
    except ValueError:
        print("❌ Состояния должны быть числами")
        return
    
    technique = args[2] if len(args) > 2 else "дыхание"
    comment = " ".join(args[3:]) if len(args) > 3 else ""
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute(
        "INSERT INTO recovery_log (before_state, after_state, technique, comment) VALUES (?, ?, ?, ?)",
        (before, after, technique, comment)
    )
    
    # Также записываем состояние после
    c.execute(
        "INSERT INTO states (state, delta, comment) VALUES (?, ?, ?)",
        (after, None, f"Recovery: {comment}")
    )
    
    conn.commit()
    conn.close()
    
    diff = after - before
    sign = "+" if diff >= 0 else ""
    print(f"✅ Recovery записан: {before} → {after} ({sign}{diff})")
    print(f"   Техника: {technique}")
    if comment:
        print(f"   Комментарий: {comment}")


def cmd_panic(args):
    """Запись панической атаки"""
    if not args or len(args) < 2:
        print("❌ Использование: python cli.py panic <before> <after> [grounding] [comment]")
        return
    
    try:
        before = int(args[0])
        after = int(args[1])
    except ValueError:
        print("❌ Состояния должны быть числами")
        return
    
    grounding = args[2] if len(args) > 2 else "5-4-3-2-1"
    comment = " ".join(args[3:]) if len(args) > 3 else ""
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute(
        "INSERT INTO panic_log (before_state, after_state, grounding_done, comment) VALUES (?, ?, ?, ?)",
        (before, after, grounding, comment)
    )
    
    c.execute(
        "INSERT INTO states (state, delta, comment) VALUES (?, ?, ?)",
        (after, "panic", comment)
    )
    
    conn.commit()
    conn.close()
    
    diff = after - before
    sign = "+" if diff >= 0 else ""
    print(f"✅ Паническая атака записана: {before} → {after} ({sign}{diff})")
    print(f"   Grounding: {grounding}")
    if comment:
        print(f"   Комментарий: {comment}")


def cmd_stats(args):
    """Показать статистику"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print("\n📊 СТАТИСТИКА")
    print("=" * 50)
    
    # Общая статистика
    c.execute("SELECT COUNT(*), ROUND(AVG(state), 2), MIN(state), MAX(state) FROM states")
    total, avg, min_s, max_s = c.fetchone()
    if total:
        print(f"Всего замеров: {total}")
        print(f"Среднее: {avg}")
        print(f"Мин/Макс: {min_s} / {max_s}")
    
    # За сегодня
    c.execute("""
        SELECT COUNT(*), ROUND(AVG(state), 2) 
        FROM states 
        WHERE DATE(timestamp) = DATE('now')
    """)
    today_count, today_avg = c.fetchone()
    print(f"\nЗа сегодня: {today_count or 0} замеров, среднее: {today_avg or 'нет'}")
    
    # Дельта сегодня
    c.execute("""
        SELECT COUNT(*) FROM states 
        WHERE DATE(timestamp) = DATE('now') AND delta = 'delta'
    """)
    delta_today = c.fetchone()[0]
    print(f"Δ Активна сегодня: {'ДА' if delta_today > 0 else 'нет'}")
    
    # Триггеры за 24ч
    c.execute("""
        SELECT code, COUNT(*) as cnt 
        FROM triggers_log 
        WHERE timestamp > datetime('now', '-1 day') AND code != '_'
        GROUP BY code ORDER BY cnt DESC
    """)
    triggers_24h = c.fetchall()
    if triggers_24h:
        print("\nТриггеры за 24ч:")
        for code, cnt in triggers_24h:
            trigger_name = TRIGGER_CODES.get(code, code)
            print(f"  {code} ({trigger_name}): {cnt}")
    
    # Последние записи
    c.execute("""
        SELECT state, delta, timestamp, comment 
        FROM states 
        ORDER BY timestamp DESC LIMIT 5
    """)
    recent = c.fetchall()
    if recent:
        print("\nПоследние 5 записей:")
        for state, delta, ts, comment in recent:
            delta_str = " Δ" if delta else ""
            print(f"  {ts}: {state}/10{delta_str} | {comment or '-'}")
    
    conn.close()
    print()


def cmd_analyze(args):
    """Анализ паттернов"""
    from core.analyzer import analyze_patterns
    analyze_patterns()


def cmd_predict(args):
    """Предсказание состояния"""
    from core.predictor import predict_state
    predict_state()


def cmd_gate(args):
    """Проверка Gate (защитный механизм)"""
    from core.gate import check_gate
    check_gate()


def cmd_export(args):
    """Экспорт данных"""
    from core.exporter import export_data
    month = args[0] if args else datetime.now().strftime("%Y-%m")
    export_data(month)


def cmd_import(args):
    """Импорт данных"""
    from core.importer import import_data
    if not args:
        print("❌ Использование: python cli.py import <путь_к_файлу.json>")
        return
    import_data(args[0])


def cmd_backup(args):
    """Резервное копирование"""
    from core.backup_manager import create_backup
    create_backup()


def cmd_help(args):
    """Справка"""
    print("""
📋 PTSD Monitor — команды:

  state <0-10> [delta] [code] [comment]  — записать состояние
  recovery <before> <after> [tech] [com] — записать recovery
  panic <before> <after> [ground] [com]  — записать паническую атаку
  
  stats       — показать статистику
  analyze     — анализ паттернов
  predict     — предсказание состояния
  gate        — проверка защитного механизма
  
  export [YYYY-MM]  — экспорт за месяц
  import <file.json> — импорт из JSON
  backup      — резервное копирование
  
  help        — эта справка
  tui         — запустить TUI интерфейс

Коды триггеров:
  TRIGGER_ABUSE     — абьюзивное взаимодействие
  TRIGGER_CONFLICT  — конфликт
  TRIGGER_LONELY    — одиночество
  TRIGGER_INTRUSIVE — навязчивые воспоминания
  TRIGGER_DEATH     — смерть, утрата
  TRIGGER_GUILT     — вина, стыд
  TRIGGER_IMPULSE   — импульсы
  TRIGGER_GENERAL   — общий триггер
  THOUGHT           — мысли о себе
  SLEEP             — проблемы со сном
  DREAM             — триггерные сны
  _                 — нет триггера
""")


def cmd_tui(args):
    """Запуск TUI"""
    print("🚀 Запуск TUI интерфейса...")
    from core.textual_app import PTSDApp
    app = PTSDApp()
    app.run()


def main():
    init_db()
    
    if len(sys.argv) < 2:
        cmd_help([])
        return
    
    command = sys.argv[1].lower()
    args = sys.argv[2:]
    
    commands = {
        "state": cmd_state,
        "recovery": cmd_recovery,
        "panic": cmd_panic,
        "stats": cmd_stats,
        "analyze": cmd_analyze,
        "predict": cmd_predict,
        "gate": cmd_gate,
        "export": cmd_export,
        "import": cmd_import,
        "backup": cmd_backup,
        "help": cmd_help,
        "tui": cmd_tui,
    }
    
    if command in commands:
        commands[command](args)
    else:
        print(f"❌ Неизвестная команда: {command}")
        print("Используйте 'python cli.py help' для справки")


if __name__ == "__main__":
    main()
