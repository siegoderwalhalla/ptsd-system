"""
Детектор аномалий: находит дни, которые сильно выбиваются из тренда.
Запуск: python ~/army_system_py/core/anomaly_detector.py
"""
import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.expanduser("~/army_system_py/army.db")

def detect():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    print("🔍 ДЕТЕКТОР АНОМАЛИЙ")
    print("=" * 50)

    # Получаем среднее состояние по дням
    c.execute("""
        SELECT DATE(timestamp) as day, ROUND(AVG(state), 2), COUNT(*), MIN(state), MAX(state)
        FROM states
        GROUP BY day
        ORDER BY day
    """)
    days = c.fetchall()

    if len(days) < 5:
        print("⚠️ Недостаточно данных (нужно минимум 5 дней с замерами)")
        conn.close()
        return

    # Считаем скользящее среднее за 5 дней
    anomalies = []
    for i in range(2, len(days) - 2):
        window = [d[1] for d in days[i-2:i+3]]
        avg = sum(window) / len(window)
        current = days[i][1]
        deviation = current - avg

        if abs(deviation) >= 2.0:  # Отклонение на 2+ балла от среднего
            anomalies.append({
                'day': days[i][0],
                'avg': current,
                'window_avg': round(avg, 2),
                'deviation': round(deviation, 2),
                'count': days[i][2],
                'min': days[i][3],
                'max': days[i][4],
            })

    if anomalies:
        print(f"⚠️  Найдено аномалий: {len(anomalies)}")
        print()
        for a in anomalies:
            direction = "📉 СНИЖЕНИЕ" if a['deviation'] < 0 else "📈 ПОВЫШЕНИЕ"
            print(f"   {a['day']}: среднее {a['avg']} (отклонение {a['deviation']:+.2f}) — {direction}")
            print(f"      Ожидалось ~{a['window_avg']}, замеров: {a['count']}, диапазон: {a['min']}–{a['max']}")

        # Ищем возможные причины (триггеры в аномальные дни)
        print(f"\n🔍 ВОЗМОЖНЫЕ ПРИЧИНЫ:")
        for a in anomalies:
            c.execute("""
                SELECT code, comment FROM triggers_log
                WHERE DATE(timestamp) = ?
                ORDER BY timestamp
            """, (a['day'],))
            triggers = c.fetchall()
            if triggers:
                print(f"   {a['day']}:")
                for t in triggers:
                    print(f"      {t[0]}: {t[1][:60]}")
            else:
                print(f"   {a['day']}: триггеры не зафиксированы")
    else:
        print("✅ Аномалий не найдено. Состояние стабильно.")

    conn.close()

if __name__ == "__main__":
    detect()
