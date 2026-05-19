"""
CLI-клиент army.py — единая точка входа в Python-версию army_system.
Запуск: python ~/army_system_py/army.py <команда> [аргументы]

Команды:
  state <число> [delta] [код] [комментарий]  — записать состояние
  analyze                                      — анализатор паттернов
  sync                                         — синхронизация с bash-системой
  validate                                     — проверка базы
  export [csv|json|md]                         — экспорт данных
  summary                                      — сводка на сегодня
  last                                         — последний замер
  report [месяц]                               — отчёт за месяц
  dashboard                                    — дашборд (curses)
  help                                         — справка
"""
import sqlite3
import os
import sys
from datetime import datetime

DB_PATH = os.path.expanduser("~/army_system_py/army.db")
CORE_DIR = os.path.expanduser("~/army_system_py/core")

def run_lua_plugin(plugin_name, func_name, args):
    import subprocess
    plugin_path = os.path.expanduser(f"~/army_system_py/plugins/{plugin_name}")
    if not os.path.exists(plugin_path):
        return None
    lua_args = ", ".join([f"'{a}'" if isinstance(a, str) else str(a) for a in args])
    lua_lines = [
        f'dofile("{plugin_path}")',
        f'result = {func_name}({lua_args})',
        'if result ~= nil then',
        '    io.write(result)',
        'end'
    ]
    lua_code = "\n".join(lua_lines)
    try:
        result = subprocess.check_output(
            ["lua5.4", "-e", lua_code],
            timeout=2,
            stderr=subprocess.DEVNULL
        ).decode().strip()
        return result if result else None
    except:
        return None

def cmd_state(args):
    if not args:
        print("❌ Укажи состояние (0-10)")
        print("Пример: python army.py state 5")
        print("Пример: python army.py state 3 delta ТОШ 'триггер от разговора'")
        return

    state = int(args[0])
    if state < 0 or state > 10:
        print("❌ Состояние должно быть 0-10")
        return

    delta_input = 'delta' if 'delta' in args else 'none'
    code = '_'
    comment = ''

    trigger_codes = ['ТОШ', 'АРМ', 'ФЛБ', 'ВНТ', 'ДРГ', 'ГЛБ', 'СМЕРТЬ', 'ИМП', 'ГОР', 'ОБЩ', 'П-Я', 'МЫСЛЬ', 'СОН', 'ПРИК']
    for a in args[1:]:
        if a in trigger_codes:
            code = a
            break

    comment_parts = [a for a in args[1:] if a not in ('delta', code) and not a.isdigit()]
    if comment_parts:
        comment = ' '.join(comment_parts)

    # Авто-вызов Lua-плагина: если триггер ТОШ → дельта
    if code == 'ТОШ':
        lua_result = run_lua_plugin("auto_delta.lua", "on_trigger", [code, state])
        if lua_result == 'delta':
            delta_input = 'delta'

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO states (timestamp, state, delta) VALUES (?, ?, ?)", (now, state, delta_input))
    if code != '_' or comment:
        c.execute("INSERT INTO triggers_log (timestamp, state, code, comment) VALUES (?, ?, ?, ?)", (now, state, code, comment))
    conn.commit()

    levels = {8: "α (альфа)", 7: "α⁺", 6: "β⁻", 5: "β (бета)", 4: "β⁺", 3: "γ⁻", 2: "γ", 1: "γ⁺"}
    level = levels.get(state, str(state))
    delta_str = " Δ" if delta_input == 'delta' else ''
    print(f"✅ Записано: {state}/10 — {level}{delta_str}")

    # Вызов плагина-рекомендации
    recommendation = run_lua_plugin("gamma_alert.lua", "on_state", [state, delta_input])
    if recommendation:
        print(f"   {recommendation}")

    conn.close()

def cmd_last():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT timestamp, state, delta FROM states ORDER BY timestamp DESC LIMIT 1")
    row = c.fetchone()
    if row:
        ddays = (datetime(2026, 7, 2) - datetime.now()).days
        levels = {8: "α", 7: "α⁺", 6: "β⁻", 5: "β", 4: "β⁺", 3: "γ⁻", 2: "γ", 1: "γ⁺"}
        level = levels.get(row[1], str(row[1]))
        delta_str = " Δ активна" if row[2] == 'delta' else ''
        print(f"📊 Последний замер: {row[0]}")
        print(f"   Состояние: {row[1]}/10 — {level}{delta_str}")
        print(f"   До ДМБ: {ddays} дней")
    else:
        print("❌ Нет данных")
    conn.close()

def cmd_summary():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*), ROUND(AVG(state), 2), MIN(state), MAX(state) FROM states")
    total, avg, min_s, max_s = c.fetchone()
    c.execute("SELECT COUNT(*) FROM states WHERE DATE(timestamp) = DATE('now')")
    today = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM states WHERE delta = 'delta' AND DATE(timestamp) = DATE('now')")
    delta_today = c.fetchone()[0]
    ddays = (datetime(2026, 7, 2) - datetime.now()).days
    print("🛡️ ARMY SYSTEM — СВОДКА")
    print("=" * 30)
    print(f"   Замеров всего: {total}")
    print(f"   Среднее: {avg}")
    print(f"   Диапазон: {min_s} – {max_s}")
    print(f"   Сегодня: {today} замеров")
    print(f"   Дельта сегодня: {'активна' if delta_today > 0 else 'нет'}")
    print(f"   До ДМБ: {ddays} дней")
    conn.close()

def cmd_report(month=None):
    if not month:
        month = datetime.now().strftime("%Y-%m")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*), ROUND(AVG(state), 2), MIN(state), MAX(state) FROM states WHERE strftime('%Y-%m', timestamp) = ?", (month,))
    total, avg, min_s, max_s = c.fetchone()
    if total == 0:
        print(f"❌ Нет данных за {month}")
        conn.close()
        return
    c.execute("SELECT COUNT(*) FROM triggers_log WHERE strftime('%Y-%m', timestamp) = ?", (month,))
    trig_total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM states WHERE delta = 'delta' AND strftime('%Y-%m', timestamp) = ?", (month,))
    delta_days = c.fetchone()[0]
    c.execute("SELECT code, COUNT(*) FROM triggers_log WHERE strftime('%Y-%m', timestamp) = ? AND code != '_' GROUP BY code ORDER BY COUNT(*) DESC", (month,))
    top_triggers = c.fetchall()
    print(f"📊 ОТЧЁТ ЗА {month}")
    print("=" * 40)
    print(f"   Замеров: {total}")
    print(f"   Среднее: {avg}")
    print(f"   Минимум: {min_s}")
    print(f"   Максимум: {max_s}")
    print(f"   Триггеров: {trig_total}")
    print(f"   Замеров с дельтой: {delta_days}")
    if top_triggers:
        print(f"   Топ триггеров:")
        for code, cnt in top_triggers[:5]:
            print(f"      {code}: {cnt} раз(а)")
    conn.close()

def cmd_panic():
    os.system(f"python {CORE_DIR}/panic.py")

def cmd_recovery():
    os.system(f"python {CORE_DIR}/recovery.py")

def cmd_gate():
    os.system(f"python {CORE_DIR}/gate.py")

def cmd_anomaly():
    os.system(f"python {CORE_DIR}/anomaly_detector.py")

def cmd_correlate():
    os.system(f"python {CORE_DIR}/correlator.py")

def cmd_backup():
    os.system(f"python {CORE_DIR}/backup_manager.py")

def cmd_backup_list():
    os.system(f"python {CORE_DIR}/backup_manager.py list")

def cmd_backup_clean(args):
    n = args[0] if args else "5"
    os.system(f"python {CORE_DIR}/backup_manager.py clean {n}")

def cmd_dashboard():
    os.system(f"python {CORE_DIR}/dashboard.py")

def cmd_help():
    print(__doc__)

def main():
    if len(sys.argv) < 2:
        cmd_help()
        return

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd == "state":
        cmd_state(args)
    elif cmd == "last":
        cmd_last()
    elif cmd == "summary":
        cmd_summary()
    elif cmd == "panic":
        cmd_panic()
    elif cmd == "recovery":
        cmd_recovery()
    elif cmd == "dashboard":
        cmd_dashboard()
    elif cmd == "gate":
        cmd_gate()
    elif cmd == "anomaly":
        cmd_anomaly()
    elif cmd == "correlate":
        cmd_correlate()
    elif cmd == "backup":
        cmd_backup()
    elif cmd == "backup-list":
        cmd_backup_list()
    elif cmd == "backup-clean":
        cmd_backup_clean(args)

    elif cmd == "report":
        month = args[0] if args else None
        cmd_report(month)
    elif cmd == "analyze":
        os.system(f"python {CORE_DIR}/analyzer.py")
    elif cmd == "sync":
        os.system(f"python {CORE_DIR}/sync_bash.py")
    elif cmd == "validate":
        os.system(f"python {CORE_DIR}/validator.py")
    elif cmd == "export":
        fmt = args[0] if args else "md"
        os.system(f"python {CORE_DIR}/exporter.py {fmt}")
    elif cmd in ("help", "-h", "--help"):
        cmd_help()
    else:
        print(f"❌ Неизвестная команда: {cmd}")

if __name__ == "__main__":
    main()
