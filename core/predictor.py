"""
Предиктор состояний на чистом Python (без ML-библиотек).
Учится на истории и предсказывает состояние на завтра.
Запуск: python core/predictor.py
"""
import sqlite3
import os
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "ptsd.db"

def predict_state():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    print("🔮 ПРЕДИКТОР СОСТОЯНИЙ")
    print("=" * 40)

    # 1. Среднее по дням недели
    dow_avg = {}
    c.execute("""
        SELECT CAST(strftime('%w', timestamp) AS INTEGER), ROUND(AVG(state), 2), COUNT(*)
        FROM states
        GROUP BY strftime('%w', timestamp)
    """)
    for dow, avg_s, cnt in c.fetchall():
        dow_avg[dow] = (avg_s, cnt)

    # 2. Среднее по часам
    hour_avg = defaultdict(list)
    c.execute("""
        SELECT CAST(strftime('%H', timestamp) AS INTEGER), state
        FROM states
    """)
    for hour, state in c.fetchall():
        hour_avg[hour].append(state)

    # 3. Последние 3 дня
    c.execute("""
        SELECT DATE(timestamp), ROUND(AVG(state), 2)
        FROM states
        GROUP BY DATE(timestamp)
        ORDER BY DATE(timestamp) DESC
        LIMIT 3
    """)
    recent = c.fetchall()

    # 4. Тренд
    c.execute("""
        SELECT DATE(timestamp), ROUND(AVG(state), 2)
        FROM states
        GROUP BY DATE(timestamp)
        ORDER BY DATE(timestamp) DESC
        LIMIT 7
    """)
    week = c.fetchall()

    # 5. Последний триггер
    c.execute("""
        SELECT code, state, timestamp FROM triggers_log
        ORDER BY timestamp DESC LIMIT 1
    """)
    last_trigger = c.fetchone()

    # 6. Дельта сегодня
    c.execute("""
        SELECT COUNT(*) FROM states
        WHERE DATE(timestamp) = DATE('now') AND delta = 'delta'
    """)
    delta_active = c.fetchone()[0] > 0

    print("📊 БАЗОВЫЕ ДАННЫЕ:")
    print()

    # Среднее по дням недели
    tomorrow_dow = (datetime.now() + timedelta(days=1)).weekday()
    # Конвертируем: Python weekday (0=Пн) → SQLite strftime('%w') (0=Вс)
    sql_dow = (tomorrow_dow + 1) % 7
    dow_info = dow_avg.get(sql_dow, (None, 0))
    days_ru = ["Вс", "Пн", "Вт", "Ср", "Чт", "Пт", "Сб"]
    print(f"   Завтра: {days_ru[tomorrow_dow]}")
    if dow_info[1] > 0:
        print(f"   Среднее по этому дню недели: {dow_info[0]} ({dow_info[1]} замеров)")
    else:
        print(f"   Нет данных по этому дню недели")

    # Среднее за последние 3 дня
    if recent:
        recent_avg = sum(r[1] for r in recent) / len(recent)
        print(f"   Среднее за последние 3 дня: {round(recent_avg, 2)}")

    # Тренд
    if len(week) >= 2:
        trend = week[0][1] - week[-1][1]
        direction = "📈 РАСТЁТ" if trend > 0.5 else ("📉 ПАДАЕТ" if trend < -0.5 else "➖ СТАБИЛЬНО")
        print(f"   Тренд за неделю: {direction} ({round(trend, 2)})")

    # Дельта
    if delta_active:
        print(f"   Δ Сегодня: АКТИВНА (риск выше)")

    # Последний триггер
    if last_trigger:
        print(f"   Последний триггер: {last_trigger[0]} (состояние {last_trigger[1]})")

    # === ПРЕДСКАЗАНИЕ ===
    print()
    print("🔮 ПРЕДСКАЗАНИЕ:")

    score = 5.0  # базовое
    reasons = []

    # Вклад дня недели
    if dow_info[1] >= 3:
        dow_effect = dow_info[0] - 5.0
        score += dow_effect * 0.3
        reasons.append(f"день недели ({dow_info[0]:+.1f} к среднему)")

    # Вклад тренда
    if len(week) >= 2 and abs(trend) > 0.3:
        trend_effect = trend * 0.5
        score += trend_effect
        reasons.append(f"тренд ({trend:+.1f})")

    # Вклад последних дней
    if recent:
        recent_effect = (recent_avg - 5.0) * 0.4
        score += recent_effect
        reasons.append(f"последние дни ({recent_avg:+.1f} к среднему)")

    # Вклад дельты
    if delta_active:
        score -= 1.5
        reasons.append("дельта активна (-1.5)")

    # Вклад последнего триггера
    if last_trigger:
        if last_trigger[0] in ('TRIGGER_ABUSE', 'TRIGGER_CONFLICT'):
            score -= 1.0
            reasons.append(f"триггер {last_trigger[0]} (-1.0)")
        elif last_trigger[0] in ('TRIGGER_DEATH', 'TRIGGER_IMPULSE', 'TRIGGER_INTRUSIVE'):
            score -= 1.5
            reasons.append(f"тяжёлый триггер {last_trigger[0]} (-1.5)")

    score = max(1.0, min(10.0, score))
    score = round(score, 1)

    levels = {10: "α⁺⁺", 9: "α⁺", 8: "α", 7: "β⁻", 6: "β", 5: "β⁺", 4: "γ⁻", 3: "γ", 2: "γ⁺", 1: "γ⁺⁺"}
    level = levels.get(round(score), str(score))
    emoji = "🟢" if score >= 7 else ("🟡" if score >= 4 else "🔴")

    print(f"   Прогноз: {score}/10 — {level} {emoji}")
    if reasons:
        print(f"   Факторы: {', '.join(reasons)}")

    if score <= 3:
        print()
        print("   ⚠️  РЕКОМЕНДАЦИЯ: Высокий риск спада.")
        print("   → запланируй recovery заранее")
        print("   → избегай стрессовых ситуаций")
        print("   → предупреди близких")
    elif score <= 5:
        print()
        print("   💡 РЕКОМЕНДАЦИЯ: Средний уровень.")
        print("   → будь внимателен к триггерам")
        print("   → держи recovery под рукой")
    else:
        print()
        print("   ✅ РЕКОМЕНДАЦИЯ: Ожидается хороший день.")
        print("   → можно планировать дела")

    conn.close()

if __name__ == "__main__":
    predict_state()
