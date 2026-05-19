"""
Дашборд на Textual — современный GUI в терминале.
Запуск: python ~/army_system_py/core/textual_dashboard.py
"""
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Button
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
import sqlite3
import os
from datetime import datetime, date

DB_PATH = os.path.expanduser("~/army_system_py/army.db")

class StateWidget(Static):
    """Виджет текущего состояния"""
    def on_mount(self):
        self.update_state()

    def update_state(self):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT state, delta, timestamp FROM states ORDER BY timestamp DESC LIMIT 1")
        row = c.fetchone()
        if row:
            state, delta, ts = row
            levels = {8: "α (альфа)", 7: "α⁺", 6: "β⁻", 5: "β (бета)", 4: "β⁺", 3: "γ⁻ (тяж)", 2: "γ (тяж)", 1: "γ⁺ (пиздец)"}
            level = levels.get(state, str(state))
            delta_str = "  Δ АКТИВНА" if delta == 'delta' else ""
            ddays = (date(2026, 7, 2) - date.today()).days
            text = f"[bold]СОСТОЯНИЕ: {state}/10 — {level}{delta_str}[/bold]\n"
            text += f"Последний замер: {ts}\n"
            text += f"До ДМБ: {ddays} дней"
        else:
            text = "Нет данных"
        conn.close()
        self.update(text)

class StatsWidget(Static):
    """Виджет статистики"""
    def on_mount(self):
        self.update_stats()

    def update_stats(self):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT COUNT(*), ROUND(AVG(state), 2) FROM states")
        total, avg = c.fetchone()
        c.execute("SELECT COUNT(*) FROM triggers_log WHERE code = 'ТОШ' AND timestamp > datetime('now', '-1 day')")
        tosh24 = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM states WHERE delta = 'delta' AND DATE(timestamp) = DATE('now')")
        delta_today = c.fetchone()[0]
        text = f"[bold]СТАТИСТИКА[/bold]\n"
        text += f"Замеров: {total}\n"
        text += f"Среднее: {avg}\n"
        text += f"ТОШ за 24ч: {tosh24}\n"
        text += f"Δ сегодня: {'ДА' if delta_today > 0 else 'нет'}"
        conn.close()
        self.update(text)

class ArmyDashboard(App):
    CSS = """
    Screen {
        background: #1a1a2e;
    }
    Header {
        background: #16213e;
        color: #e94560;
    }
    .main-container {
        padding: 1;
    }
    .panel {
        border: solid #e94560;
        padding: 1;
        margin: 1;
        background: #0f3460;
        color: #ffffff;
    }
    .button-panel {
        border: solid #533483;
        padding: 1;
        margin: 1;
        background: #0f3460;
    }
    Button {
        margin: 1;
        background: #533483;
        color: #ffffff;
    }
    Footer {
        background: #16213e;
        color: #e94560;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(classes="main-container"):
            with Vertical(id="left"):
                with Container(classes="panel"):
                    yield StateWidget(id="state")
                with Container(classes="panel"):
                    yield StatsWidget(id="stats")
            with Vertical(id="right"):
                with Container(classes="button-panel"):
                    yield Static("[bold]ДЕЙСТВИЯ[/bold]")
                    yield Button("📊 State (записать)", id="btn_state", variant="primary")
                    yield Button("🔄 Recovery", id="btn_recovery", variant="default")
                    yield Button("🚪 Gate", id="btn_gate", variant="warning")
                    yield Button("📈 Анализ", id="btn_analyze", variant="default")
                    yield Button("🔄 Обновить", id="btn_refresh", variant="default")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed):
        btn = event.button.id
        if btn == "btn_refresh":
            self.query_one("#state", StateWidget).update_state()
            self.query_one("#stats", StatsWidget).update_stats()
        elif btn == "btn_state":
            self.exit()
            os.system("python ~/army_system_py/army.py state")
        elif btn == "btn_recovery":
            self.exit()
            os.system("python ~/army_system_py/core/recovery.py")
        elif btn == "btn_gate":
            self.exit()
            os.system("python ~/army_system_py/army.py gate")
        elif btn == "btn_analyze":
            self.exit()
            os.system("python ~/army_system_py/army.py analyze")

if __name__ == "__main__":
    app = ArmyDashboard()
    app.run()
