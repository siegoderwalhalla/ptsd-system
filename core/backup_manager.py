"""
Бэкап-менеджер: создаёт и управляет резервными копиями базы данных.
Запуск: python core/backup_manager.py
        python core/backup_manager.py list
        python core/backup_manager.py clean 5
"""
import sqlite3
import os
import shutil
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "ptsd.db")
BACKUP_DIR = os.path.join(os.path.dirname(__file__), "..", "backups")

def create_backup():
    if not os.path.exists(DB_PATH):
        print("❌ База данных не найдена")
        return None

    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"ptsd_backup_{timestamp}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_name)

    shutil.copy2(DB_PATH, backup_path)
    print(f"✅ Бэкап создан: {backup_name}")
    return backup_path

def list_backups():
    if not os.path.exists(BACKUP_DIR):
        print("📂 Папка с бэкапами пуста")
        return

    files = sorted(os.listdir(BACKUP_DIR), reverse=True)
    print(f"📂 Бэкапы ({len(files)} шт.):")
    for f in files:
        path = os.path.join(BACKUP_DIR, f)
        size_kb = os.path.getsize(path) // 1024
        print(f"   {f} ({size_kb} КБ)")

def clean_old_backups(keep=5):
    if not os.path.exists(BACKUP_DIR):
        print("📂 Папка с бэкапами пуста")
        return

    files = sorted(os.listdir(BACKUP_DIR))
    if len(files) <= keep:
        print(f"✅ Всего {len(files)} бэкапов, нечего удалять (лимит {keep})")
        return

    to_delete = files[:-keep]
    for f in to_delete:
        os.remove(os.path.join(BACKUP_DIR, f))
    print(f"✅ Удалено {len(to_delete)} старых бэкапов, оставлено {keep}")

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "create"

    if cmd == "list":
        list_backups()
    elif cmd == "clean":
        keep = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        clean_old_backups(keep)
    else:
        create_backup()
