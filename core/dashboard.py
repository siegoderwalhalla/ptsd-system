import curses
import sqlite3
import os
from datetime import datetime, date

DB_PATH = os.path.expanduser("~/army_system_py/army.db")
WIDTH = 60

def init_colors():
    curses.start_color()
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(6, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    curses.init_pair(7, curses.COLOR_BLACK, curses.COLOR_WHITE)

def fetch_data():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT timestamp, state, delta FROM states ORDER BY timestamp DESC LIMIT 1")
    last = c.fetchone()

    c.execute("SELECT ROUND(AVG(state), 2) FROM states")
    avg = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM states WHERE DATE(timestamp) = DATE('now')")
    today = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM states WHERE delta = 'delta' AND DATE(timestamp) = DATE('now')")
    delta_today = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM triggers_log WHERE code = 'ТОШ' AND timestamp > datetime('now', '-1 day')")
    tosh_24 = c.fetchone()[0]

    c.execute("""
        SELECT DATE(timestamp) as day, ROUND(AVG(state), 2)
        FROM states
        GROUP BY day
        ORDER BY day DESC
        LIMIT 7
    """)
    history = list(reversed(c.fetchall()))

    c.execute("""
        SELECT code, timestamp, comment FROM triggers_log
        ORDER BY timestamp DESC LIMIT 5
    """)
    triggers = list(reversed(c.fetchall()))

    conn.close()

    return {
        'last': last,
        'avg': avg,
        'today': today,
        'delta_today': delta_today,
        'tosh_24': tosh_24,
        'history': history,
        'triggers': triggers,
    }

def draw_bar(stdscr, y, x, value, max_val, width, color):
    filled = int(value * width / max_val) if max_val > 0 else 0
    bar = "█" * filled + "░" * (width - filled)
    stdscr.addstr(y, x, bar, curses.color_pair(color))

def draw_graph(stdscr, y, x, history, height, width):
    if not history:
        stdscr.addstr(y + 1, x, "Нет данных", curses.color_pair(4))
        return

    vals = [h[1] for h in history]
    max_v, min_v = max(vals), min(vals)
    if max_v == min_v:
        max_v = min_v + 1

    for row in range(height):
        level = max_v - (max_v - min_v) * row / (height - 1)
        label = f"{level:.0f}┤" if row == 0 or row == height - 1 else "  │"
        try:
            stdscr.addstr(y + row, x, label, curses.color_pair(4))
        except curses.error: pass

    for i, (day, val) in enumerate(history):
        col = x + 3 + i * 2
        row = y + height - 1 - int((val - min_v) / (max_v - min_v) * (height - 1))
        try:
            color = 3 if val >= 7 else 2 if val >= 4 else 1
            stdscr.addstr(row, col, "●", curses.color_pair(color) | curses.A_BOLD)
            stdscr.addstr(y + height, col - 1, day[-2:], curses.color_pair(4))
        except curses.error: pass

def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(1)
    init_colors()

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        data = fetch_data()
        ddays = (date(2026, 7, 2) - date.today()).days

        try:
            stdscr.addstr(0, 2, "🛡️ ARMY SYSTEM — DASHBOARD", curses.color_pair(7) | curses.A_BOLD)
            now = datetime.now().strftime("%H:%M:%S")
            stdscr.addstr(0, w - 10, now, curses.color_pair(4))
        except curses.error: pass

        try:
            stdscr.addstr(2, 2, "═" * (w - 4), curses.color_pair(4))
        except curses.error: pass

        if data['last']:
            ts, state, delta = data['last']
            levels = {8: "α", 7: "α⁺", 6: "β⁻", 5: "β", 4: "β⁺", 3: "γ⁻", 2: "γ", 1: "γ⁺"}
            level = levels.get(state, str(state))
            delta_str = " Δ" if delta == 'delta' else ''
            color = 3 if state >= 7 else 2 if state >= 4 else 1
            try:
                stdscr.addstr(3, 2, f"СОСТОЯНИЕ: {state}/10 — {level}{delta_str}", curses.color_pair(color) | curses.A_BOLD)
                stdscr.addstr(3, 35, f"🏠 ДМБ: {ddays} дней", curses.color_pair(5) | curses.A_BOLD)
                stdscr.addstr(3, 55, f"Замер: {ts}", curses.color_pair(4))
            except curses.error: pass
            draw_bar(stdscr, 4, 2, 10 - state, 10, 30, color)
            try:
                stdscr.addstr(4, 34, f"{state}/10", curses.color_pair(color) | curses.A_BOLD)
            except curses.error: pass

        try:
            stdscr.addstr(6, 2, "═" * (w - 4), curses.color_pair(4))
            stdscr.addstr(7, 2, "ГРАФИК (7 дней)", curses.A_BOLD)
        except curses.error: pass
        draw_graph(stdscr, 8, 2, data['history'], 5, 30)

        # Правая панель
        px = min(w - 25, 58)
        try:
            stdscr.addstr(3, px, f"Замеров сегодня: {data['today']}", curses.color_pair(5))
            stdscr.addstr(4, px, f"Δ активна: {'ДА' if data['delta_today'] > 0 else 'нет'}", curses.color_pair(6 if data['delta_today'] > 0 else 3))
            stdscr.addstr(5, px, f"ТОШ за 24ч: {data['tosh_24']}", curses.color_pair(1 if data['tosh_24'] > 0 else 3))
            stdscr.addstr(6, px, f"Среднее: {data['avg']}", curses.color_pair(4))
        except curses.error: pass

        try:
            stdscr.addstr(15, 2, "═" * (w - 4), curses.color_pair(4))
            stdscr.addstr(16, 2, "ПОСЛЕДНИЕ ТРИГГЕРЫ", curses.A_BOLD)
        except curses.error: pass
        for i, (code, ts, comment) in enumerate(data['triggers']):
            try:
                line = f"  {ts} | {code:6} | {comment[:40]}"
                stdscr.addstr(17 + i, 2, line[:w-2], curses.color_pair(4))
            except curses.error: pass

        try:
            stdscr.addstr(h - 1, 2, "Q — выход | R — обновить", curses.color_pair(4))
        except curses.error: pass

        stdscr.refresh()
        key = stdscr.getch()
        if key == ord('q'):
            break
        elif key == ord('r'):
            continue

        import time
        time.sleep(0.5)

curses.wrapper(main)
