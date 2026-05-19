"""
Главное меню Python-версии army_system.
Запуск: python ~/army_system_py/menu.py
"""
import os
import subprocess
import sys

CORE_DIR = os.path.expanduser("~/army_system_py/core")
ARMY_PY = os.path.expanduser("~/army_system_py/army.py")

def clear():
    os.system('clear')

def run(cmd):
    """Запускает команду через subprocess, чтобы меню не глотало ввод"""
    subprocess.call(["python", ARMY_PY] + cmd.split())

def run_raw(script_name):
    """Запускает скрипт напрямую"""
    subprocess.call(["python", os.path.join(CORE_DIR, script_name)])

def main():
    while True:
        clear()
        print("╔══════════════════════════════════════╗")
        print("║   🛡️ ARMY SYSTEM — PYTHON EDITION    ║")
        print("╚══════════════════════════════════════╝")
        print()
        print("  📊 СОСТОЯНИЕ")
        print("    1) state        — записать состояние")
        print("    2) last         — последний замер")
        print("    3) summary      — сводка на сегодня")
        print("    4) dashboard    — дашборд (curses)")
        print()
        print("  🚨 ЭКСТРЕННОЕ")
        print("    5) panic        — антипанический протокол")
        print("    6) recovery     — восстановление")
        print("    7) gate         — шлюз безопасности")
        print()
    print("  🔮 ПРОГНОЗ")
    print("   17) predict      — предсказать состояние на завтра")

        print("  🧠 АНАЛИЗ")
        print("    8) analyze      — анализатор паттернов")
        print("    9) anomaly      — детектор аномалий")
        print("   10) correlate    — коррелятор связей")
        print("   11) report       — отчёт за месяц")
        print()
        print("  ⚙️  ДАННЫЕ")
        print("   12) sync         — синхронизация с bash")
        print("   13) validate     — проверка базы")
        print("   14) export       — экспорт (CSV/JSON/MD)")
        print("   15) backup       — создать бэкап")
        print("   16) backup-list  — список бэкапов")
        print()
        print("    0) 🚪 выход")
        print()

        choice = input("  Выбор: ").strip()

        if choice == "0":
            print("🛡️ Выход.")
            break
        elif choice == "1":
            state = input("  Состояние (0-10): ").strip()
            extra = input("  Дельта/код/комментарий (Enter если нет): ").strip()
            cmd_parts = ["state", state]
            if extra:
                cmd_parts.extend(extra.split())
            subprocess.call(["python", ARMY_PY] + cmd_parts)
        elif choice == "2":
            run("last")
        elif choice == "3":
            run("summary")
        elif choice == "4":
            run_raw("dashboard.py")
        elif choice == "5":
            run_raw("panic.py")
        elif choice == "6":
            run_raw("recovery.py")
        elif choice == "7":
            run("gate")
        elif choice == "8":
            run("analyze")
        elif choice == "9":
            run("anomaly")
        elif choice == "10":
            run("correlate")
        elif choice == "11":
            month = input("  Месяц (ГГГГ-ММ, Enter для текущего): ").strip()
            run(f"report {month}")
        elif choice == "12":
            run("sync")
        elif choice == "13":
            run("validate")
        elif choice == "14":
            fmt = input("  Формат (csv/json/md, Enter для md): ").strip() or "md"
            run(f"export {fmt}")
        elif choice == "15":
            run("backup")
        elif choice == "17":
            run_raw("predictor.py")

        elif choice == "16":
            run("backup-list")
        else:
            print("Неверный выбор.")

        input("\n  Нажми Enter чтобы вернуться...")

if __name__ == "__main__":
    main()
