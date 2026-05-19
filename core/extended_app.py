"""
ARMY SYSTEM — расширенная версия с дополнительными экранами.
Запуск: python ~/army_system_py/core/extended_app.py
Выход: Ctrl+Q или кнопка «Выход»
"""
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Button, Input, Label, TextArea
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.screen import Screen
import sqlite3, os, subprocess, io, sys, random, json
from datetime import datetime, date

DB_PATH = os.path.expanduser("~/army_system_py/army.db")
ARMY_PY = os.path.expanduser("~/army_system_py/army.py")
CORE_DIR = os.path.expanduser("~/army_system_py/core")

def run_python_script(path):
    old_stdout, sys.stdout = sys.stdout, io.StringIO()
    try: exec(open(path).read())
    except: pass
    result = sys.stdout.getvalue(); sys.stdout = old_stdout
    return result

# ═══════════════════ ЭКРАНЫ ═══════════════════
class DashboardScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal():
            with Vertical(id="left"):
                with Container(classes="panel"): yield Static(id="state_info")
                with Container(classes="panel"): yield Static(id="stats_info")
                with Container(classes="panel"): yield Static(id="graph_info")
            with Vertical(id="right"):
                with Container(classes="button-panel"):
                    yield Static("[bold reverse] НАВИГАЦИЯ [/]")
                    for label, sid in [("📊 Записать", "btn_state"), ("🔄 Recovery", "btn_recovery"),
                         ("🚨 Panic", "btn_panic"), ("🚪 Gate", "btn_gate"),
                         ("📈 Анализ", "btn_analyze"), ("🔮 Прогноз", "btn_predict"),
                         ("📋 Отчёт", "btn_report"), ("📝 Дневник", "btn_journal"),
                         ("📈 Тренды", "btn_trends"), ("🎯 Триггеры", "btn_triggers"),
                         ("🔔 Напоминания", "btn_reminders"), ("🟢 Быстрый state", "btn_quick"), ("🌤 Погода", "btn_weather"),
                         ("🔄 Обновить", "btn_refresh")]:
                        yield Button(label, id=sid, variant="primary" if sid == "btn_state" else "default")
                    yield Button("🚪 Выход", id="btn_exit", variant="error")
        yield Footer()

    def on_mount(self): self.refresh_dashboard()
    def refresh_dashboard(self):
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("SELECT state, delta, timestamp FROM states ORDER BY timestamp DESC LIMIT 1")
        row = c.fetchone()
        if row:
            state, delta, ts = row
            levels = {8: "α (альфа)", 7: "α⁺", 6: "β⁻", 5: "β (бета)", 4: "β⁺", 3: "γ⁻ (тяж)", 2: "γ (тяж)", 1: "γ⁺ (пиздец)"}
            level = levels.get(state, str(state))
            delta_str = "  Δ АКТИВНА" if delta == 'delta' else ""
            ddays = (date(2026, 7, 2) - date.today()).days
            state_text = f"[bold]СОСТОЯНИЕ: {state}/10 — {level}{delta_str}[/bold]\nЗамер: {ts}\nДо ДМБ: {ddays} дней"
        else: state_text = "Нет данных"
        c.execute("SELECT COUNT(*), ROUND(AVG(state), 2) FROM states")
        total, avg = c.fetchone()
        c.execute("SELECT COUNT(*) FROM triggers_log WHERE code = 'ТОШ' AND timestamp > datetime('now', '-1 day')")
        tosh24 = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM states WHERE delta = 'delta' AND DATE(timestamp) = DATE('now')")
        delta_today = c.fetchone()[0]
        stats_text = f"[bold]СТАТИСТИКА[/bold]\nЗамеров: {total} | Среднее: {avg}\nТОШ за 24ч: {tosh24} | Δ сегодня: {'ДА' if delta_today > 0 else 'нет'}"
        c.execute("SELECT DATE(timestamp) as d, ROUND(AVG(state), 2) FROM states GROUP BY d ORDER BY d DESC LIMIT 7")
        hist = list(reversed(c.fetchall()))
        graph_text = "[bold]ГРАФИК (7 дней)[/bold]\n"
        if hist:
            max_v, min_v = max(h[1] for h in hist), min(h[1] for h in hist)
            if max_v == min_v: max_v = min_v + 1
            for hh in hist:
                day, val = hh
                bar_len = max(1, int((val - min_v) / (max_v - min_v) * 20))
                bar, emoji = "█" * bar_len, "🟢" if val >= 7 else ("🟡" if val >= 4 else "🔴")
                graph_text += f"{day[-5:]}: {bar} {val} {emoji}\n"
        else: graph_text += "Нет данных"
        conn.close()
        self.query_one("#state_info", Static).update(state_text)
        self.query_one("#stats_info", Static).update(stats_text)
        self.query_one("#graph_info", Static).update(graph_text)

    def on_button_pressed(self, event: Button.Pressed):
        btn = event.button.id
        screens = {"btn_state": StateScreen, "btn_recovery": RecoveryScreen, "btn_panic": PanicScreen,
                   "btn_gate": GateScreen, "btn_analyze": AnalyzeScreen, "btn_predict": PredictScreen,
                   "btn_report": ReportScreen, "btn_journal": JournalScreen, "btn_trends": TrendsScreen,
                   "btn_triggers": TriggersScreen, "btn_reminders": RemindersScreen, "btn_quick": QuickStateScreen}
        if btn == "btn_refresh": self.refresh_dashboard()
        elif btn == "btn_exit": self.app.exit()
        elif btn in screens: self.app.push_screen(screens[btn]())

# ═══════════════════ ЭКРАНЫ 2-8 (существующие) ═══════════════════
class StateScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(classes="panel"):
            yield Static("[bold]📊 ЗАПИСЬ СОСТОЯНИЯ[/bold]\n")
            for label, pid, placeholder in [("Состояние (0-10):", "input_state", "5"),
                ("Дельта? (y/n):", "input_delta", "n"), ("Код триггера:", "input_code", "ТОШ / _"),
                ("Комментарий:", "input_comment", "как ты?")]:
                yield Label(label); yield Input(placeholder=placeholder, id=pid)
            yield Button("✅ Сохранить", id="btn_save", variant="primary"); yield Button("🔙 Назад", id="btn_back")
        yield Footer()
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn_back": self.dismiss()
        elif event.button.id == "btn_save":
            state = self.query_one("#input_state", Input).value or "5"
            delta = "delta" if self.query_one("#input_delta", Input).value.lower() == "y" else ""
            code = self.query_one("#input_code", Input).value or "_"
            comment = self.query_one("#input_comment", Input).value or ""
            subprocess.call(["python", ARMY_PY, "state", state] + ([delta] if delta else []) + [code, comment])
            self.dismiss()

class RecoveryScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(classes="panel"):
            yield Static("[bold]🔄 RECOVERY[/bold]\nДыхание: вдох 4 сек → выдох 6 сек. 6 циклов.\n")
            yield Label("Состояние после:"); yield Input(placeholder="6", id="rec_state")
            yield Label("Ощущения:"); yield Input(placeholder="стало легче", id="rec_comment")
            yield Button("✅ Сохранить", id="btn_save", variant="primary"); yield Button("🔙 Назад", id="btn_back")
        yield Footer()
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn_back": self.dismiss()
        elif event.button.id == "btn_save":
            state = self.query_one("#rec_state", Input).value or "6"
            comment = self.query_one("#rec_comment", Input).value or ""
            subprocess.call(["python", ARMY_PY, "state", state, "RECOVERY", comment]); self.dismiss()

class PanicScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(classes="panel"):
            yield Static("[bold]🚨 PANIC[/bold]\nGrounding 5-4-3-2-1. Дыхание 4-4-6, 5 циклов.\n")
            yield Label("Состояние после:"); yield Input(placeholder="3", id="panic_state")
            yield Label("Ощущения:"); yield Input(placeholder="страх", id="panic_comment")
            yield Button("✅ Сохранить", id="btn_save", variant="error"); yield Button("🔙 Назад", id="btn_back")
        yield Footer()
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn_back": self.dismiss()
        elif event.button.id == "btn_save":
            state = self.query_one("#panic_state", Input).value or "3"
            comment = self.query_one("#panic_comment", Input).value or ""
            subprocess.call(["python", ARMY_PY, "state", state, "PANIC", comment]); self.dismiss()

class GateScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(classes="panel"):
            yield Static("[bold]🚪 TOSHA GATE[/bold]\n"); yield Static(id="gate_result"); yield Static("\n")
            yield Button("🔄 Обновить", id="btn_refresh"); yield Button("🔙 Назад", id="btn_back")
        yield Footer()
    def on_mount(self): self.refresh()
    def refresh(self):
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("SELECT state, delta FROM states ORDER BY timestamp DESC LIMIT 1")
        row = c.fetchone(); text = ""
        if row:
            state, delta = row
            c.execute("SELECT COUNT(*) FROM triggers_log WHERE code='ТОШ' AND timestamp > datetime('now','-1 day')")
            tosh24 = c.fetchone()[0]
            block, reason = 0, ""
            if state <= 2: block, reason = 1, "КРИТИЧЕСКОЕ"
            elif state <= 3: block, reason = 1, "ТЯЖЁЛОЕ"
            elif delta == 'delta' and state <= 5: block, reason = 1, "ДЕЛЬТА"
            elif tosh24 >= 3: block, reason = 1, "МНОГО ТОШ"
            elif state <= 4: block, reason = 2, "ПОНИЖЕННОЕ"
            elif state <= 5: block, reason = 2, "СРЕДНЕЕ"
            text = f"⛔ ЗАБЛОКИРОВАН ({reason})" if block == 1 else (f"⚠️ ОГРАНИЧЕН ({reason})" if block == 2 else "✅ РАЗРЕШЁН")
        else: text = "Нет данных"
        conn.close(); self.query_one("#gate_result", Static).update(text)
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn_back": self.dismiss()
        elif event.button.id == "btn_refresh": self.refresh()

class AnalyzeScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with ScrollableContainer(classes="panel"):
            yield Static("[bold]📈 АНАЛИЗ[/bold]\n"); yield Static(id="result")
        with Container(classes="button-panel"):
            yield Button("🔄 Обновить", id="btn_refresh"); yield Button("🔙 Назад", id="btn_back")
        yield Footer()
    def on_mount(self): self.refresh()
    def refresh(self):
        self.query_one("#result", Static).update(run_python_script(os.path.join(CORE_DIR, "analyzer.py"))[:2000])
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn_back": self.dismiss()
        elif event.button.id == "btn_refresh": self.refresh()

class PredictScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(classes="panel"):
            yield Static("[bold]🔮 ПРОГНОЗ[/bold]\n"); yield Static(id="result")
        with Container(classes="button-panel"):
            yield Button("🔄 Обновить", id="btn_refresh"); yield Button("🔙 Назад", id="btn_back")
        yield Footer()
    def on_mount(self): self.refresh()
    def refresh(self):
        import io, sys
        old_stdout, sys.stdout = sys.stdout, io.StringIO()
        try:
            import importlib.util, os
            spec = importlib.util.spec_from_file_location("predictor", os.path.join(CORE_DIR, "predictor.py"))
            predictor = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(predictor); predictor.predict()
        except: pass
        result = sys.stdout.getvalue(); sys.stdout = old_stdout
        self.query_one("#result", Static).update(result or "Нет данных")
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn_back": self.dismiss()
        elif event.button.id == "btn_refresh": self.refresh()

class ReportScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(classes="panel"):
            yield Static("[bold]📋 ОТЧЁТ[/bold]\n"); yield Label("Месяц (ГГГГ-ММ):")
            yield Input(placeholder=datetime.now().strftime("%Y-%m"), id="month"); yield Static(id="result")
        with Container(classes="button-panel"):
            yield Button("📋 Показать", id="btn_show", variant="primary"); yield Button("🔙 Назад", id="btn_back")
        yield Footer()
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn_back": self.dismiss()
        elif event.button.id == "btn_show":
            month = self.query_one("#month", Input).value or datetime.now().strftime("%Y-%m")
            old_stdout, sys.stdout = sys.stdout, io.StringIO()
            try:
                conn = sqlite3.connect(DB_PATH); c = conn.cursor()
                c.execute("SELECT COUNT(*), ROUND(AVG(state),2), MIN(state), MAX(state) FROM states WHERE strftime('%Y-%m', timestamp)=?", (month,))
                total, avg, min_s, max_s = c.fetchone()
                if total == 0: print(f"Нет данных за {month}")
                else:
                    print(f"Замеров: {total} | Среднее: {avg} | Мин: {min_s} | Макс: {max_s}")
                    c.execute("SELECT code, COUNT(*) FROM triggers_log WHERE strftime('%Y-%m', timestamp)=? AND code!='_' GROUP BY code ORDER BY COUNT(*) DESC", (month,))
                    for code, cnt in c.fetchall(): print(f"  {code}: {cnt}")
                conn.close()
            except: pass
            self.query_one("#result", Static).update(sys.stdout.getvalue()); sys.stdout = old_stdout

# ═══════════════════ НОВЫЕ ЭКРАНЫ ═══════════════════

# 📝 ДНЕВНИК
class JournalScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(classes="panel"):
            yield Static("[bold]📝 ДНЕВНИК[/bold]\n")
            yield TextArea(id="journal_entry", text="")
            yield Button("💾 Сохранить", id="btn_save", variant="primary")
            yield Button("📖 Последние записи", id="btn_view")
            yield Button("🔙 Назад", id="btn_back")
        yield Footer()
    def on_mount(self):
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS journal (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, entry TEXT)")
        conn.commit(); conn.close()
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn_back": self.dismiss()
        elif event.button.id == "btn_save":
            entry = self.query_one("#journal_entry", TextArea).text.strip()
            if entry:
                conn = sqlite3.connect(DB_PATH); c = conn.cursor()
                c.execute("INSERT INTO journal (timestamp, entry) VALUES (?, ?)", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), entry))
                conn.commit(); conn.close()
                self.query_one("#journal_entry", TextArea).text = ""
                self.app.push_screen(MessageScreen("✅ Запись сохранена!"))
        elif event.button.id == "btn_view": self.app.push_screen(JournalViewScreen())

class JournalViewScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with ScrollableContainer(classes="panel"):
            yield Static("[bold]📖 ПОСЛЕДНИЕ ЗАПИСИ[/bold]\n")
            yield Static(id="entries")
        with Container(classes="button-panel"):
            yield Button("🔙 Назад", id="btn_back")
        yield Footer()
    def on_mount(self):
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("SELECT timestamp, entry FROM journal ORDER BY timestamp DESC LIMIT 10")
        rows = c.fetchall(); conn.close()
        text = "\n".join([f"[bold]{r[0]}[/bold]\n{r[1]}\n" for r in rows]) if rows else "Записей пока нет."
        self.query_one("#entries", Static).update(text)
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn_back": self.dismiss()

# 📈 ТРЕНДЫ
class TrendsScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(classes="panel"):
            yield Static("[bold]📈 ТРЕНДЫ[/bold]\n")
            yield Static(id="trends_result")
        with Container(classes="button-panel"):
            yield Button("🔙 Назад", id="btn_back")
        yield Footer()
    def on_mount(self):
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("SELECT strftime('%Y-W%W', timestamp) as week, ROUND(AVG(state),2), COUNT(*) FROM states GROUP BY week ORDER BY week DESC LIMIT 4")
        rows = c.fetchall()
        text = "Неделя   | Среднее | Замеров | Тренд\n"
        prev = None
        for week, avg, cnt in reversed(rows):
            arrow = ""
            if prev is not None:
                arrow = "📈" if avg > prev else ("📉" if avg < prev else "➖")
            text += f"{week} | {avg:7} | {cnt:7} | {arrow}\n"
            prev = avg
        conn.close()
        self.query_one("#trends_result", Static).update(text)
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn_back": self.dismiss()

# 🎯 ТРИГГЕРЫ
class TriggersScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(classes="panel"):
            yield Static("[bold]🎯 ТРИГГЕРЫ[/bold]\n")
            yield Label("Фильтр по коду (Enter = все):")
            yield Input(placeholder="ТОШ", id="filter_code")
            yield Static(id="triggers_result")
        with Container(classes="button-panel"):
            yield Button("🔍 Показать", id="btn_show", variant="primary")
            yield Button("🔙 Назад", id="btn_back")
        yield Footer()
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn_back": self.dismiss()
        elif event.button.id == "btn_show":
            code = self.query_one("#filter_code", Input).value.strip()
            conn = sqlite3.connect(DB_PATH); c = conn.cursor()
            if code:
                c.execute("SELECT timestamp, state, comment FROM triggers_log WHERE code=? ORDER BY timestamp DESC LIMIT 20", (code,))
            else:
                c.execute("SELECT timestamp, code, state, comment FROM triggers_log ORDER BY timestamp DESC LIMIT 20")
            rows = c.fetchall(); conn.close()
            text = "\n".join([f"{' '.join(map(str, r))}" for r in rows]) if rows else "Ничего не найдено."
            self.query_one("#triggers_result", Static).update(text)

# 🔔 НАПОМИНАНИЯ
class RemindersScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(classes="panel"):
            yield Static("[bold]🔔 НАПОМИНАНИЯ[/bold]\n")
            yield Static("Что помогает:\n• Recovery (дыхание 4-6)\n• Турник до боли\n• Дневник — вылить агрессию\n• Прогулка / строевая\n• Водный баланс\n")
            yield Button("✅ Отметить выполненное", id="btn_done", variant="primary")
            yield Button("🔙 Назад", id="btn_back")
        yield Footer()
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn_back": self.dismiss()
        elif event.button.id == "btn_done":
            conn = sqlite3.connect(DB_PATH); c = conn.cursor()
            c.execute("CREATE TABLE IF NOT EXISTS reminders_log (timestamp TEXT, action TEXT)")
            c.execute("INSERT INTO reminders_log VALUES (?, ?)", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "done"))
            conn.commit(); conn.close()
            self.app.push_screen(MessageScreen("✅ Отмечено!"))

# 🟢 БЫСТРЫЙ STATE
class QuickStateScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(classes="panel"):
            yield Static("[bold]🟢 БЫСТРЫЙ STATE[/bold]\nНажми цифру — состояние запишется мгновенно.\n")
            for i in range(1, 11):
                yield Button(str(i), id=f"qs_{i}", variant="primary" if i >= 7 else ("warning" if i >= 4 else "error"))
            yield Button("🔙 Назад", id="btn_back")
        yield Footer()
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn_back": self.dismiss()
        elif event.button.id.startswith("qs_"):
            state = event.button.id.split("_")[1]
            subprocess.call(["python", ARMY_PY, "state", state])
            self.app.push_screen(MessageScreen(f"✅ Записано: {state}/10"))


# 🌤 ПОГОДА
class WeatherScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(classes="panel"):
            yield Static("[bold]🌤 ПОГОДА[/bold]
")
            yield Label("Город (латиницей):")
            yield Input(placeholder="Moscow", id="city_input")
            yield Static(id="weather_result")
        with Container(classes="button-panel"):
            yield Button("🔍 Узнать погоду", id="btn_weather_show", variant="primary")
            yield Button("🔙 Назад", id="btn_weather_back")
        yield Footer()
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn_weather_back": self.dismiss()
        elif event.button.id == "btn_weather_show":
            city = self.query_one("#city_input", Input).value.strip() or "Moscow"
            try:
                import subprocess, json
                raw = subprocess.check_output(["curl", "-s", "--connect-timeout", "3", f"https://wttr.in/{city}?format=j1&lang=ru"], timeout=5).decode()
                data = json.loads(raw)
                c = data["current_condition"][0]
                text = f"Город: {city}
Температура: {c['temp_C']}°C (ощущается {c['FeelsLikeC']}°C)
{c['weatherDesc'][0]['value']}
Влажность: {c['humidity']}%
Ветер: {c['windspeedKmph']} км/ч
Давление: {c['pressure']} hPa"
            except Exception as e:
                text = f"Ошибка: {e}"
            self.query_one("#weather_result", Static).update(text)


# 💬 СООБЩЕНИЕ
class MessageScreen(Screen):
    def __init__(self, message):
        super().__init__()
        self.message = message
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(classes="panel"):
            yield Static(f"[bold]{self.message}[/bold]\n")
            yield Button("OK", id="btn_ok", variant="primary")
        yield Footer()
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn_ok": self.dismiss()

# ═══════════════════ ГЛАВНОЕ ПРИЛОЖЕНИЕ ═══════════════════
class ArmyApp(App):
    CSS = """
    Screen { background: #1a1a2e; }
    Header { background: #16213e; color: #e94560; }
    .panel { border: solid #e94560; padding: 1; margin: 1; background: #0f3460; color: #ffffff; }
    .button-panel { border: solid #533483; padding: 1; margin: 1; background: #0f3460; }
    Button { margin: 1; }
    Input { margin: 1; background: #1a1a2e; color: #ffffff; }
    Label { margin: 1; color: #e94560; }
    TextArea { margin: 1; background: #1a1a2e; color: #ffffff; height: 10; }
    Footer { background: #16213e; color: #e94560; }
    """
    SCREENS = {"dashboard": DashboardScreen}
    def on_mount(self):
        self.push_screen("dashboard")

if __name__ == "__main__":
    ArmyApp().run()
