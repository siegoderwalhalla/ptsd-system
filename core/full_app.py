#!/usr/bin/env python3
"""
ARMY SYSTEM — полное приложение (16 экранов).
Запуск: army
"""
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Button, Input, Label, TextArea
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.screen import Screen
import sqlite3, os, subprocess, io, sys, random, json
import importlib.util
import importlib.util
from datetime import datetime, date

DB_PATH = os.path.expanduser("~/army_system_py/army.db")
ARMY_PY = os.path.expanduser("~/army_system_py/army.py")
CORE_DIR = os.path.expanduser("~/army_system_py/core")

QUOTES = [
    "«Не трать время на мысли о том, чего у тебя нет.» — Марк Аврелий",
    "«Препятствие становится путём.» — Марк Аврелий",
    "«То, что нас не убивает, делает нас сильнее.» — Ницше",
    "«Если крыша ржавая, то подвал всегда мокрый.» — Албанская мудрость",
    "«Почему кабинет информатики на третьем этаже?» — Вяч Жум",
    "«Думай о том, что ты смертен.» — Марк Аврелий",
    "«Я не хочу умирать. Я хочу жить.» — Castle Eclipse",
    "«Не подавлять. Не обесценивать. Принимать.» — Castle Eclipse",
]

def run_python_script(path):
    old_stdout, sys.stdout = sys.stdout, io.StringIO()
    try: exec(open(path).read())
    except: pass
    result = sys.stdout.getvalue(); sys.stdout = old_stdout
    return result

# ═══════════════════ ДАШБОРД ═══════════════════
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
                    yield Static("[bold reverse] ОСНОВНОЕ [/]")
                    for label, sid, var in [
                        ("📊 Записать", "btn_state", "primary"), ("🔄 Recovery", "btn_recovery", "default"),
                        ("🚨 Panic", "btn_panic", "error"), ("🚪 Gate", "btn_gate", "warning"),
                        ("📈 Анализ", "btn_analyze", "default"), ("🔮 Прогноз", "btn_predict", "default"),
                        ("📋 Отчёт", "btn_report", "default"), ("📝 Дневник", "btn_journal", "default"),
                        ("🟢 Быстрый state", "btn_quick", "default"), ("🔄 Обновить", "btn_refresh", "default"),
                    ]:
                        yield Button(label, id=sid, variant=var)
                    yield Static("")
                    yield Static("[bold reverse] ИНСТРУМЕНТЫ [/]")
                    for label, sid in [
                        ("📈 Тренды", "btn_trends"), ("🎯 Триггеры", "btn_triggers"),
                        ("📅 Таймлайн", "btn_timeline2"), ("📊 Сравнение", "btn_compare"),
                        ("🇩🇪 Немецкий", "btn_german"), ("📥 Импорт", "btn_import"),
                        ("🌤 Погода", "btn_weather"), ("💬 Цитата", "btn_quote"),
                        ("🔔 Напоминания", "btn_reminders"),
                    ]:
                        yield Button(label, id=sid, variant="default")
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
            total_days = 365; passed = total_days - ddays; pct = int(passed / total_days * 20)
            bar = "▓" * pct + "░" * (20 - pct)
            state_text = f"[bold]СОСТОЯНИЕ: {state}/10 — {level}{delta_str}[/bold]\nЗамер: {ts}\nДо ДМБ: {ddays} дней\n[{bar}] {int(passed/total_days*100)}%"
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
        screens = {
            "btn_state": StateScreen, "btn_recovery": RecoveryScreen, "btn_panic": PanicScreen,
            "btn_gate": GateScreen, "btn_analyze": AnalyzeScreen, "btn_predict": PredictScreen,
            "btn_report": ReportScreen, "btn_journal": JournalScreen, "btn_trends": TrendsScreen,
            "btn_triggers": TriggersScreen, "btn_reminders": RemindersScreen,
            "btn_quick": QuickStateScreen, "btn_weather": WeatherScreen, "btn_quote": QuoteScreen,
            "btn_timeline2": TimelineScreen, "btn_compare": CompareScreen,
            "btn_german": GermanScreen, "btn_import": ImportScreen,
        }
        if btn == "btn_refresh": self.refresh_dashboard()
        elif btn == "btn_exit": self.app.exit()
        elif btn in screens: self.app.push_screen(screens[btn]())

class StateScreen(Screen):
    def compose(self): yield Header(show_clock=True); yield Container(classes="panel"); yield Static("[bold]📊 ЗАПИСЬ[/bold]\n"); yield Label("Состояние (0-10):"); yield Input(placeholder="5", id="s"); yield Label("Дельта? (y/n):"); yield Input(placeholder="n", id="d"); yield Label("Код:"); yield Input(placeholder="ТОШ", id="c"); yield Label("Комментарий:"); yield Input(placeholder="...", id="m"); yield Button("✅ Сохранить", id="save", variant="primary"); yield Button("🔙 Назад", id="back"); yield Footer()
    def on_button_pressed(self, e):
        if e.button.id == "back": self.dismiss()
        elif e.button.id == "save":
            s = self.query_one("#s", Input).value or "5"
            d = "delta" if self.query_one("#d", Input).value.lower() == "y" else ""
            c = self.query_one("#c", Input).value or "_"
            m = self.query_one("#m", Input).value or ""
            subprocess.call(["python", ARMY_PY, "state", s] + ([d] if d else []) + [c, m])
            if int(s) <= 3:
                try:
                    subprocess.call(["termux-notification", "--title", "⚠️ ГАММА", "--content", f"Состояние {s}/10. Сделай recovery.", "--priority", "max"])
                except: pass
            self.dismiss()

class RecoveryScreen(Screen):
    def compose(self): yield Header(show_clock=True); yield Container(classes="panel"); yield Static("[bold]🔄 RECOVERY[/bold]\nДыхание 4-6, 6 циклов.\n"); yield Label("Состояние:"); yield Input(placeholder="6", id="s"); yield Label("Ощущения:"); yield Input(placeholder="...", id="m"); yield Button("✅ Сохранить", id="save", variant="primary"); yield Button("🔙 Назад", id="back"); yield Footer()
    def on_button_pressed(self, e):
        if e.button.id == "back": self.dismiss()
        elif e.button.id == "save":
            s = self.query_one("#s", Input).value or "6"; m = self.query_one("#m", Input).value or ""
            subprocess.call(["python", ARMY_PY, "state", s, "RECOVERY", m]); self.dismiss()

class PanicScreen(Screen):
    def compose(self): yield Header(show_clock=True); yield Container(classes="panel"); yield Static("[bold]🚨 PANIC[/bold]\nGrounding 5-4-3-2-1. Дыхание 4-4-6, 5 циклов.\n"); yield Label("Состояние:"); yield Input(placeholder="3", id="s"); yield Label("Ощущения:"); yield Input(placeholder="...", id="m"); yield Button("✅ Сохранить", id="save", variant="error"); yield Button("🔙 Назад", id="back"); yield Footer()
    def on_button_pressed(self, e):
        if e.button.id == "back": self.dismiss()
        elif e.button.id == "save":
            s = self.query_one("#s", Input).value or "3"; m = self.query_one("#m", Input).value or ""
            subprocess.call(["python", ARMY_PY, "state", s, "PANIC", m]); self.dismiss()

class GateScreen(Screen):
    def compose(self): yield Header(show_clock=True); yield Container(classes="panel"); yield Static("[bold]🚪 GATE[/bold]\n"); yield Static(id="r"); yield Button("🔄 Обновить", id="ref"); yield Button("🔙 Назад", id="back"); yield Footer()
    def on_mount(self): self.call_after_refresh(self.do_refresh)
    def do_refresh(self):
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("SELECT state, delta FROM states ORDER BY timestamp DESC LIMIT 1"); row = c.fetchone(); text = ""
        if row:
            s, d = row; c.execute("SELECT COUNT(*) FROM triggers_log WHERE code='ТОШ' AND timestamp > datetime('now','-1 day')"); t24 = c.fetchone()[0]
            bl, rs = 0, ""
            if s <= 2: bl, rs = 1, "КРИТИЧЕСКОЕ"
            elif s <= 3: bl, rs = 1, "ТЯЖЁЛОЕ"
            elif d == 'delta' and s <= 5: bl, rs = 1, "ДЕЛЬТА"
            elif t24 >= 3: bl, rs = 1, "МНОГО ТОШ"
            elif s <= 4: bl, rs = 2, "ПОНИЖЕННОЕ"
            elif s <= 5: bl, rs = 2, "СРЕДНЕЕ"
            text = f"⛔ ЗАБЛОКИРОВАН ({rs})" if bl == 1 else (f"⚠️ ОГРАНИЧЕН ({rs})" if bl == 2 else "✅ РАЗРЕШЁН")
        else: text = "Нет данных"
        conn.close(); self.query_one("#r", Static).update(text)
    def on_button_pressed(self, e):
        if e.button.id == "back": self.dismiss()
        elif e.button.id == "ref": self.refresh()

class AnalyzeScreen(Screen):
    def compose(self):
        yield Header(show_clock=True)
        with ScrollableContainer(classes="panel"):
            yield Static("[bold]📈 АНАЛИЗ[/bold]\n")
            yield Static(id="r", classes="output")
        with Container(classes="button-panel"):
            yield Button("🔄 Обновить", id="ref")
            yield Button("🔙 Назад", id="back")
        yield Footer()

    def on_mount(self):
        self.call_after_refresh(self.do_refresh)

    def do_refresh(self):
        try:
            result = run_python_script(os.path.join(CORE_DIR, "analyzer.py"))
            self.query_one("#r", Static).update(result[:2500])
        except Exception as e:
            error_text = f"Ошибка анализа:\n{str(e)[:400]}"
            try:
                self.query_one("#r", Static).update(error_text)
            except:
                pass

    def on_button_pressed(self, e):
        if e.button.id == "back":
            self.dismiss()
        elif e.button.id == "ref":
            self.do_refresh()

class PredictScreen(Screen):
    def compose(self): yield Header(show_clock=True); yield Container(classes="panel"); yield Static("[bold]🔮 ПРОГНОЗ[/bold]\n"); yield Static(id="r"); yield Container(classes="button-panel"); yield Button("🔄 Обновить", id="ref"); yield Button("🔙 Назад", id="back"); yield Footer()
    def on_mount(self): self.call_after_refresh(self.do_refresh)
    def do_refresh(self):
        import importlib.util
        old_stdout, sys.stdout = sys.stdout, io.StringIO()
        try:
            spec = importlib.util.spec_from_file_location("predictor", os.path.join(CORE_DIR, "predictor.py"))
            m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); m.predict()
        except: pass
        r = sys.stdout.getvalue(); sys.stdout = old_stdout
        self.query_one("#r", Static).update(r or "Нет данных")
    def on_button_pressed(self, e):
        if e.button.id == "back": self.dismiss()
        elif e.button.id == "ref": self.refresh()

class ReportScreen(Screen):
    def compose(self): yield Header(show_clock=True); yield Container(classes="panel"); yield Static("[bold]📋 ОТЧЁТ[/bold]\n"); yield Label("Месяц (ГГГГ-ММ):"); yield Input(placeholder=datetime.now().strftime("%Y-%m"), id="m"); yield Static(id="r"); yield Container(classes="button-panel"); yield Button("📋 Показать", id="show", variant="primary"); yield Button("🔙 Назад", id="back"); yield Footer()
    def on_button_pressed(self, e):
        if e.button.id == "back": self.dismiss()
        elif e.button.id == "show":
            m = self.query_one("#m", Input).value or datetime.now().strftime("%Y-%m")
            old_stdout, sys.stdout = sys.stdout, io.StringIO()
            try:
                conn = sqlite3.connect(DB_PATH); c = conn.cursor()
                c.execute("SELECT COUNT(*), ROUND(AVG(state),2), MIN(state), MAX(state) FROM states WHERE strftime('%Y-%m', timestamp)=?", (m,))
                t, a, mn, mx = c.fetchone()
                if t == 0: print(f"Нет данных за {m}")
                else:
                    print(f"Замеров: {t} | Среднее: {a} | Мин: {mn} | Макс: {mx}")
                    c.execute("SELECT code, COUNT(*) FROM triggers_log WHERE strftime('%Y-%m', timestamp)=? AND code!='_' GROUP BY code ORDER BY COUNT(*) DESC", (m,))
                    for cd, cn in c.fetchall(): print(f"  {cd}: {cn}")
                conn.close()
            except: pass
            self.query_one("#r", Static).update(sys.stdout.getvalue()); sys.stdout = old_stdout

class JournalScreen(Screen):
    def compose(self): yield Header(show_clock=True); yield Container(classes="panel"); yield Static("[bold]📝 ДНЕВНИК[/bold]\n"); yield TextArea(id="t"); yield Button("💾 Сохранить", id="save", variant="primary"); yield Button("📖 Последние записи", id="view"); yield Button("🔙 Назад", id="back"); yield Footer()
    def on_mount(self):
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS journal (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, entry TEXT)")
        conn.commit(); conn.close()
    def on_button_pressed(self, e):
        if e.button.id == "back": self.dismiss()
        elif e.button.id == "save":
            t = self.query_one("#t", TextArea).text.strip()
            if t:
                conn = sqlite3.connect(DB_PATH); c = conn.cursor()
                c.execute("INSERT INTO journal (timestamp, entry) VALUES (?, ?)", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), t))
                conn.commit(); conn.close(); self.query_one("#t", TextArea).text = ""
                self.app.push_screen(MessageScreen("✅ Запись сохранена!"))
        elif e.button.id == "view": self.app.push_screen(JournalViewScreen())

class JournalViewScreen(Screen):
    def compose(self): yield Header(show_clock=True); yield ScrollableContainer(classes="panel"); yield Static("[bold]📖 ЗАПИСИ[/bold]\n"); yield Static(id="r"); yield Container(classes="button-panel"); yield Button("🔙 Назад", id="back"); yield Footer()
    def on_mount(self):
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("SELECT timestamp, entry FROM journal ORDER BY timestamp DESC LIMIT 10"); rows = c.fetchall(); conn.close()
        self.query_one("#r", Static).update("\n".join([f"[bold]{r[0]}[/bold]\n{r[1]}\n" for r in rows]) if rows else "Записей нет.")
    def on_button_pressed(self, e):
        if e.button.id == "back": self.dismiss()

class TrendsScreen(Screen):
    def compose(self): yield Header(show_clock=True); yield Container(classes="panel"); yield Static("[bold]📈 ТРЕНДЫ[/bold]\n"); yield Static(id="r"); yield Container(classes="button-panel"); yield Button("🔙 Назад", id="back"); yield Footer()
    def on_mount(self):
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("SELECT strftime('%Y-W%W', timestamp) as w, ROUND(AVG(state),2), COUNT(*) FROM states GROUP BY w ORDER BY w DESC LIMIT 4")
        rows = c.fetchall(); prev = None; text = "Неделя   | Ср. | Замеров | Тренд\n"
        for w, a, n in reversed(rows):
            arrow = "" if prev is None else ("📈" if a > prev else ("📉" if a < prev else "➖"))
            text += f"{w} | {a:4} | {n:7} | {arrow}\n"; prev = a
        conn.close(); self.query_one("#r", Static).update(text)
    def on_button_pressed(self, e):
        if e.button.id == "back": self.dismiss()

class TriggersScreen(Screen):
    def compose(self): yield Header(show_clock=True); yield Container(classes="panel"); yield Static("[bold]🎯 ТРИГГЕРЫ[/bold]\n"); yield Label("Фильтр:"); yield Input(placeholder="ТОШ", id="f"); yield Static(id="r"); yield Container(classes="button-panel"); yield Button("🔍 Показать", id="show", variant="primary"); yield Button("🔙 Назад", id="back"); yield Footer()
    def on_button_pressed(self, e):
        if e.button.id == "back": self.dismiss()
        elif e.button.id == "show":
            f = self.query_one("#f", Input).value.strip()
            conn = sqlite3.connect(DB_PATH); c = conn.cursor()
            if f: c.execute("SELECT timestamp, state, comment FROM triggers_log WHERE code=? ORDER BY timestamp DESC LIMIT 20", (f,))
            else: c.execute("SELECT timestamp, code, state, comment FROM triggers_log ORDER BY timestamp DESC LIMIT 20")
            rows = c.fetchall(); conn.close()
            self.query_one("#r", Static).update("\n".join([" ".join(map(str, r)) for r in rows]) if rows else "Ничего не найдено.")

class RemindersScreen(Screen):
    def compose(self):
        yield Header(show_clock=True)
        with Container(classes="panel"):
            yield Static("[bold]🔔 НАПОМИНАНИЯ[/bold]\n\nRecovery • Турник • Дневник • Прогулка • Вода\n")
            yield Button("✅ Отметить", id="done", variant="primary")
            yield Button("⏰ Напомнить через 30 мин", id="remind30")
            yield Button("🔙 Назад", id="back")
        yield Footer()
    def on_button_pressed(self, e):
        if e.button.id == "back":
            self.dismiss()
        elif e.button.id == "done":
            conn = sqlite3.connect(DB_PATH); c = conn.cursor()
            c.execute("CREATE TABLE IF NOT EXISTS reminders_log (timestamp TEXT, action TEXT)")
            c.execute("INSERT INTO reminders_log VALUES (?, ?)", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "done"))
            conn.commit(); conn.close()
            self.app.push_screen(MessageScreen("✅ Отмечено!"))
        elif e.button.id == "remind30":
            try:
                subprocess.call(["termux-notification", "--title", "ARMY SYSTEM", "--content", "Проверь состояние! Сделай замер.", "--priority", "high"])
                self.app.push_screen(MessageScreen("✅ Уведомление отправлено"))
            except:
                self.app.push_screen(MessageScreen("❌ Termux:API не установлен"))

class QuickStateScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(classes="panel"):
            yield Static("[bold]🟢 БЫСТРЫЙ STATE[/bold]\nНажми цифру:\n")
            for i in range(1, 11):
                yield Button(str(i), id=f"qs_{i}", variant="primary" if i >= 7 else ("warning" if i >= 4 else "error"))
            yield Button("🔙 Назад", id="back")
        yield Footer()
    def on_button_pressed(self, e):
        if e.button.id == "back": self.dismiss()
        elif e.button.id.startswith("qs_"):
            s = e.button.id.split("_")[1]; subprocess.call(["python", ARMY_PY, "state", s])
            self.app.push_screen(MessageScreen(f"✅ Записано: {s}/10"))

class WeatherScreen(Screen):
    def compose(self): yield Header(show_clock=True); yield Container(classes="panel"); yield Static("[bold]🌤 ПОГОДА[/bold]\n"); yield Label("Город (латиницей):"); yield Input(placeholder="Moscow", id="city"); yield Static(id="r", markup=False); yield Container(classes="button-panel"); yield Button("🔍 Узнать", id="show", variant="primary"); yield Button("🔙 Назад", id="back"); yield Footer()
    def on_button_pressed(self, e):
        if e.button.id == "back": self.dismiss()
        elif e.button.id == "show":
            city = self.query_one("#city", Input).value.strip() or "Moscow"
            try:
                import urllib.request, ssl
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                req = urllib.request.Request(f"http://wttr.in/{city}?format=j1&lang=ru", headers={"User-Agent": "curl/7.0"})
                raw = urllib.request.urlopen(req, context=ctx, timeout=15).read().decode()
                data = json.loads(raw); c = data["current_condition"][0]
                text = f"{city}: {c['weatherDesc'][0]['value']}, {c['temp_C']}C, {c['humidity']}%"
            except Exception as ex:
                text = f"Ошибка: {str(ex)[:100]}"
            self.query_one("#r", Static).update(text)

class QuoteScreen(Screen):
    def compose(self): yield Header(show_clock=True); yield Container(classes="panel"); yield Static("[bold]💬 ЦИТАТА[/bold]\n"); yield Static(random.choice(QUOTES), id="q"); yield Button("🎲 Ещё", id="more"); yield Button("🔙 Назад", id="back"); yield Footer()
    def on_button_pressed(self, e):
        if e.button.id == "back": self.dismiss()
        elif e.button.id == "more": self.query_one("#q", Static).update(random.choice(QUOTES))

class MessageScreen(Screen):
    def __init__(self, msg): super().__init__(); self.msg = msg
    def compose(self): yield Header(show_clock=True); yield Container(classes="panel"); yield Static(f"[bold]{self.msg}[/bold]\n"); yield Button("OK", id="ok", variant="primary"); yield Footer()
    def on_button_pressed(self, e):
        if e.button.id == "ok": self.dismiss()


class TimelineScreen(Screen):
    def compose(self):
        yield Header(show_clock=True)
        with Container(classes="panel"):
            yield Static("[bold]📅 ТАЙМЛАЙН[/bold]\n")
            yield Label("Дата (ГГГГ-ММ-ДД, Enter = сегодня):")
            yield Input(placeholder=datetime.now().strftime("%Y-%m-%d"), id="tl_date")
            yield Static(id="tl_result")
        with Container(classes="button-panel"):
            yield Button("🔍 Показать", id="tl_show", variant="primary")
            yield Button("🔙 Назад", id="tl_back")
        yield Footer()

    def on_button_pressed(self, e):
        if e.button.id == "tl_back": self.dismiss()
        elif e.button.id == "tl_show":
            d = self.query_one("#tl_date", Input).value.strip() or datetime.now().strftime("%Y-%m-%d")
            conn = sqlite3.connect(DB_PATH); c = conn.cursor()
            c.execute("SELECT timestamp, state, delta FROM states WHERE DATE(timestamp)=? ORDER BY timestamp", (d,))
            states = c.fetchall()
            c.execute("SELECT timestamp, code, comment FROM triggers_log WHERE DATE(timestamp)=? ORDER BY timestamp", (d,))
            triggers = c.fetchall()
            c.execute("SELECT timestamp, entry FROM journal WHERE DATE(timestamp)=? ORDER BY timestamp", (d,))
            journal = c.fetchall()
            conn.close()
            text = f"[bold]Таймлайн за {d}[/bold]\n\n"
            if states:
                text += "[bold]📊 Замеры:[/bold]\n"
                for ts, st, dl in states:
                    dl_str = " Δ" if dl == 'delta' else ""
                    text += f"  {ts[-8:]}: {st}/10{dl_str}\n"
            if triggers:
                text += "\n[bold]🎯 Триггеры:[/bold]\n"
                for ts, cd, cm in triggers:
                    text += f"  {ts[-8:]}: {cd} — {cm[:60]}\n"
            if journal:
                text += "\n[bold]📝 Дневник:[/bold]\n"
                for ts, entry in journal:
                    text += f"  {ts[-8:]}: {entry[:80]}\n"
            if not states and not triggers and not journal:
                text += "Нет данных за этот день."
            self.query_one("#tl_result", Static).update(text)

class CompareScreen(Screen):
    def compose(self):
        yield Header(show_clock=True)
        with Container(classes="panel"):
            yield Static("[bold]📊 СРАВНЕНИЕ ПЕРИОДОВ[/bold]\n")
            yield Label("Период 1 (ГГГГ-ММ):")
            yield Input(placeholder="2026-04", id="p1")
            yield Label("Период 2 (ГГГГ-ММ):")
            yield Input(placeholder="2026-05", id="p2")
            yield Static(id="cmp_result")
        with Container(classes="button-panel"):
            yield Button("📊 Сравнить", id="cmp_show", variant="primary")
            yield Button("🔙 Назад", id="cmp_back")
        yield Footer()

    def on_button_pressed(self, e):
        if e.button.id == "cmp_back": self.dismiss()
        elif e.button.id == "cmp_show":
            p1 = self.query_one("#p1", Input).value.strip() or "2026-04"
            p2 = self.query_one("#p2", Input).value.strip() or "2026-05"
            conn = sqlite3.connect(DB_PATH); c = conn.cursor()
            text = "[bold]СРАВНЕНИЕ[/bold]\n\n"
            for p, label in [(p1, "Период 1"), (p2, "Период 2")]:
                c.execute("SELECT COUNT(*), ROUND(AVG(state),2), MIN(state), MAX(state) FROM states WHERE strftime('%Y-%m', timestamp)=?", (p,))
                t, a, mn, mx = c.fetchone()
                c.execute("SELECT COUNT(*) FROM triggers_log WHERE strftime('%Y-%m', timestamp)=? AND code='ТОШ'", (p,))
                tosh = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM states WHERE delta='delta' AND strftime('%Y-%m', timestamp)=?", (p,))
                delta = c.fetchone()[0]
                text += f"[bold]{label} ({p}):[/bold]\n"
                text += f"  Замеров: {t}, Среднее: {a}, Диапазон: {mn}-{mx}\n"
                text += f"  ТОШ: {tosh}, Δ: {delta}\n\n"
            conn.close()
            self.query_one("#cmp_result", Static).update(text)

class GermanScreen(Screen):
    def compose(self):
        yield Header(show_clock=True)
        with Container(classes="panel"):
            yield Static("[bold]🇩🇪 НЕМЕЦКИЙ[/bold]\n")
            yield Static(id="ger_word")
            yield Input(placeholder="перевод", id="ger_input")
            yield Static(id="ger_result")
        with Container(classes="button-panel"):
            yield Button("✅ Проверить", id="ger_check", variant="primary")
            yield Button("🎲 Следующее", id="ger_next")
            yield Button("🔙 Назад", id="ger_back")
        yield Footer()

    def on_mount(self):
        self.load_words()
        self.next_word()

    def load_words(self):
        words_path = os.path.expanduser("~/army_system/german/der-woerter.md")
        self.words = []
        if os.path.exists(words_path):
            with open(words_path) as f:
                for line in f:
                    if line.startswith("|") and not line.startswith("| Wort") and not line.startswith("|------"):
                        parts = [p.strip() for p in line.split("|")]
                        if len(parts) >= 4 and parts[1] and parts[3]:
                            self.words.append({"de": parts[1], "ru": parts[3], "art": parts[2]})

    def next_word(self):
        if self.words:
            w = random.choice(self.words)
            self.current = w
            self.query_one("#ger_word", Static).update(f"[bold]{w['art']} {w['de']}[/bold]")
            self.query_one("#ger_input", Input).value = ""
            self.query_one("#ger_result", Static).update("")

    def on_button_pressed(self, e):
        if e.button.id == "ger_back": self.dismiss()
        elif e.button.id == "ger_next": self.next_word()
        elif e.button.id == "ger_check":
            answer = self.query_one("#ger_input", Input).value.strip().lower()
            correct = self.current['ru'].lower()
            if answer and (answer in correct or correct in answer):
                self.query_one("#ger_result", Static).update(f"[green]✅ Правильно! {self.current['de']} = {self.current['ru']}[/green]")
            else:
                self.query_one("#ger_result", Static).update(f"[red]❌ {self.current['de']} = {self.current['ru']}[/red]")

class ImportScreen(Screen):
    def compose(self):
        yield Header(show_clock=True)
        with Container(classes="panel"):
            yield Static("[bold]📥 ИМПОРТ ИЗ БЛОКНОТА[/bold]\n")
            yield Static("Формат: ДД.ММ.ГГГГ|ЧЧ:ММ|КОД|ощущения|действия|время_спада|тяжесть|комментарий\n")
            yield TextArea(id="import_text", text="")
            yield Static(id="import_result")
        with Container(classes="button-panel"):
            yield Button("📥 Импортировать", id="imp_do", variant="primary")
            yield Button("🔙 Назад", id="imp_back")
        yield Footer()

    def on_button_pressed(self, e):
        if e.button.id == "imp_back": self.dismiss()
        elif e.button.id == "imp_do":
            text = self.query_one("#import_text", TextArea).text.strip()
            if not text:
                self.query_one("#import_result", Static).update("Вставь данные для импорта.")
                return
            count = 0
            for line in text.split("\n"):
                line = line.strip()
                if not line: continue
                parts = line.split("|")
                if len(parts) < 7: continue
                try:
                    date_raw, time_raw = parts[0], parts[1]
                    day, month, year = date_raw.split(".")
                    date_str = f"{year}-{month}-{day} {time_raw}:00"
                    code = parts[2]
                    grade = parts[6].strip()
                    grade_map = {"альфа":8,"альфа-плюс":7,"бета-минус":6,"бета":5,"бета-плюс":4,"гамма-минус":3,"гамма":2,"гамма-плюс":1}
                    state = grade_map.get(grade, 5)
                    comment = parts[3][:100] if len(parts) > 3 else ""
                    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
                    c.execute("INSERT INTO states (timestamp, state, delta) VALUES (?, ?, ?)", (date_str, state, 'none'))
                    c.execute("INSERT INTO triggers_log (timestamp, state, code, comment) VALUES (?, ?, ?, ?)", (date_str, state, code, comment))
                    conn.commit(); conn.close()
                    count += 1
                except Exception as ex:
                    pass
            self.query_one("#import_result", Static).update(f"✅ Импортировано: {count} записей")
            self.query_one("#import_text", TextArea).text = ""


class TimelineScreen(Screen):
    def compose(self):
        yield Header(show_clock=True)
        with Container(classes="panel"):
            yield Static("[bold]📅 ТАЙМЛАЙН[/bold]\n")
            yield Label("Дата (ГГГГ-ММ-ДД, Enter = сегодня):")
            yield Input(placeholder=datetime.now().strftime("%Y-%m-%d"), id="tl_date")
            yield Static(id="tl_result")
        with Container(classes="button-panel"):
            yield Button("🔍 Показать", id="tl_show", variant="primary")
            yield Button("🔙 Назад", id="tl_back")
        yield Footer()

    def on_button_pressed(self, e):
        if e.button.id == "tl_back": self.dismiss()
        elif e.button.id == "tl_show":
            d = self.query_one("#tl_date", Input).value.strip() or datetime.now().strftime("%Y-%m-%d")
            conn = sqlite3.connect(DB_PATH); c = conn.cursor()
            c.execute("SELECT timestamp, state, delta FROM states WHERE DATE(timestamp)=? ORDER BY timestamp", (d,))
            states = c.fetchall()
            c.execute("SELECT timestamp, code, comment FROM triggers_log WHERE DATE(timestamp)=? ORDER BY timestamp", (d,))
            triggers = c.fetchall()
            c.execute("SELECT timestamp, entry FROM journal WHERE DATE(timestamp)=? ORDER BY timestamp", (d,))
            journal = c.fetchall()
            conn.close()
            text = f"[bold]Таймлайн за {d}[/bold]\n\n"
            if states:
                text += "[bold]📊 Замеры:[/bold]\n"
                for ts, st, dl in states:
                    dl_str = " Δ" if dl == 'delta' else ""
                    text += f"  {ts[-8:]}: {st}/10{dl_str}\n"
            if triggers:
                text += "\n[bold]🎯 Триггеры:[/bold]\n"
                for ts, cd, cm in triggers:
                    text += f"  {ts[-8:]}: {cd} — {cm[:60]}\n"
            if journal:
                text += "\n[bold]📝 Дневник:[/bold]\n"
                for ts, entry in journal:
                    text += f"  {ts[-8:]}: {entry[:80]}\n"
            if not states and not triggers and not journal:
                text += "Нет данных за этот день."
            self.query_one("#tl_result", Static).update(text)

class CompareScreen(Screen):
    def compose(self):
        yield Header(show_clock=True)
        with Container(classes="panel"):
            yield Static("[bold]📊 СРАВНЕНИЕ ПЕРИОДОВ[/bold]\n")
            yield Label("Период 1 (ГГГГ-ММ):")
            yield Input(placeholder="2026-04", id="p1")
            yield Label("Период 2 (ГГГГ-ММ):")
            yield Input(placeholder="2026-05", id="p2")
            yield Static(id="cmp_result")
        with Container(classes="button-panel"):
            yield Button("📊 Сравнить", id="cmp_show", variant="primary")
            yield Button("🔙 Назад", id="cmp_back")
        yield Footer()

    def on_button_pressed(self, e):
        if e.button.id == "cmp_back": self.dismiss()
        elif e.button.id == "cmp_show":
            p1 = self.query_one("#p1", Input).value.strip() or "2026-04"
            p2 = self.query_one("#p2", Input).value.strip() or "2026-05"
            conn = sqlite3.connect(DB_PATH); c = conn.cursor()
            text = "[bold]СРАВНЕНИЕ[/bold]\n\n"
            for p, label in [(p1, "Период 1"), (p2, "Период 2")]:
                c.execute("SELECT COUNT(*), ROUND(AVG(state),2), MIN(state), MAX(state) FROM states WHERE strftime('%Y-%m', timestamp)=?", (p,))
                t, a, mn, mx = c.fetchone()
                c.execute("SELECT COUNT(*) FROM triggers_log WHERE strftime('%Y-%m', timestamp)=? AND code='ТОШ'", (p,))
                tosh = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM states WHERE delta='delta' AND strftime('%Y-%m', timestamp)=?", (p,))
                delta = c.fetchone()[0]
                text += f"[bold]{label} ({p}):[/bold]\n"
                text += f"  Замеров: {t}, Среднее: {a}, Диапазон: {mn}-{mx}\n"
                text += f"  ТОШ: {tosh}, Δ: {delta}\n\n"
            conn.close()
            self.query_one("#cmp_result", Static).update(text)

class GermanScreen(Screen):
    def compose(self):
        yield Header(show_clock=True)
        with Container(classes="panel"):
            yield Static("[bold]🇩🇪 НЕМЕЦКИЙ[/bold]\n")
            yield Static(id="ger_word")
            yield Input(placeholder="перевод", id="ger_input")
            yield Static(id="ger_result")
        with Container(classes="button-panel"):
            yield Button("✅ Проверить", id="ger_check", variant="primary")
            yield Button("🎲 Следующее", id="ger_next")
            yield Button("🔙 Назад", id="ger_back")
        yield Footer()

    def on_mount(self):
        self.load_words()
        self.next_word()

    def load_words(self):
        words_path = os.path.expanduser("~/army_system/german/der-woerter.md")
        self.words = []
        if os.path.exists(words_path):
            with open(words_path) as f:
                for line in f:
                    if line.startswith("|") and not line.startswith("| Wort") and not line.startswith("|------"):
                        parts = [p.strip() for p in line.split("|")]
                        if len(parts) >= 4 and parts[1] and parts[3]:
                            self.words.append({"de": parts[1], "ru": parts[3], "art": parts[2]})

    def next_word(self):
        if self.words:
            w = random.choice(self.words)
            self.current = w
            self.query_one("#ger_word", Static).update(f"[bold]{w['art']} {w['de']}[/bold]")
            self.query_one("#ger_input", Input).value = ""
            self.query_one("#ger_result", Static).update("")

    def on_button_pressed(self, e):
        if e.button.id == "ger_back": self.dismiss()
        elif e.button.id == "ger_next": self.next_word()
        elif e.button.id == "ger_check":
            answer = self.query_one("#ger_input", Input).value.strip().lower()
            correct = self.current['ru'].lower()
            if answer and (answer in correct or correct in answer):
                self.query_one("#ger_result", Static).update(f"[green]✅ Правильно! {self.current['de']} = {self.current['ru']}[/green]")
            else:
                self.query_one("#ger_result", Static).update(f"[red]❌ {self.current['de']} = {self.current['ru']}[/red]")

class ImportScreen(Screen):
    def compose(self):
        yield Header(show_clock=True)
        with Container(classes="panel"):
            yield Static("[bold]📥 ИМПОРТ ИЗ БЛОКНОТА[/bold]\n")
            yield Static("Формат: ДД.ММ.ГГГГ|ЧЧ:ММ|КОД|ощущения|действия|время_спада|тяжесть|комментарий\n")
            yield TextArea(id="import_text", text="")
            yield Static(id="import_result")
        with Container(classes="button-panel"):
            yield Button("📥 Импортировать", id="imp_do", variant="primary")
            yield Button("🔙 Назад", id="imp_back")
        yield Footer()

    def on_button_pressed(self, e):
        if e.button.id == "imp_back": self.dismiss()
        elif e.button.id == "imp_do":
            text = self.query_one("#import_text", TextArea).text.strip()
            if not text:
                self.query_one("#import_result", Static).update("Вставь данные для импорта.")
                return
            count = 0
            for line in text.split("\n"):
                line = line.strip()
                if not line: continue
                parts = line.split("|")
                if len(parts) < 7: continue
                try:
                    date_raw, time_raw = parts[0], parts[1]
                    day, month, year = date_raw.split(".")
                    date_str = f"{year}-{month}-{day} {time_raw}:00"
                    code = parts[2]
                    grade = parts[6].strip()
                    grade_map = {"альфа":8,"альфа-плюс":7,"бета-минус":6,"бета":5,"бета-плюс":4,"гамма-минус":3,"гамма":2,"гамма-плюс":1}
                    state = grade_map.get(grade, 5)
                    comment = parts[3][:100] if len(parts) > 3 else ""
                    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
                    c.execute("INSERT INTO states (timestamp, state, delta) VALUES (?, ?, ?)", (date_str, state, 'none'))
                    c.execute("INSERT INTO triggers_log (timestamp, state, code, comment) VALUES (?, ?, ?, ?)", (date_str, state, code, comment))
                    conn.commit(); conn.close()
                    count += 1
                except Exception as ex:
                    pass
            self.query_one("#import_result", Static).update(f"✅ Импортировано: {count} записей")
            self.query_one("#import_text", TextArea).text = ""

# ═══════════════════ ПРИЛОЖЕНИЕ ═══════════════════
class SplashScreen(Screen):
    """Экран-заставка с ASCII-артом"""
    def compose(self):
        yield Header(show_clock=True)
        with Container(classes="panel"):
            yield Static(
                "[bold yellow]\n"
                "  ██████╗ █████╗ ███████╗████████╗██╗     ███████╗\n"
                " ██╔════╝██╔══██╗██╔════╝╚══██╔══╝██║     ██╔════╝\n"
                " ██║     ███████║███████╗   ██║   ██║     █████╗  \n"
                " ██║     ██╔══██║╚════██║   ██║   ██║     ██╔══╝  \n"
                " ╚██████╗██║  ██║███████║   ██║   ███████╗███████╗\n"
                "  ╚═════╝╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝╚══════╝\n"
                "[/bold yellow]\n"
                "[bold]ARMY SYSTEM — Python Edition[/bold]\n"
                "ДМБ: 2 июля 2026\n\n"
                "[italic]Нажми любую кнопку для входа...[/italic]"
            )
        yield Footer()

    def on_key(self, event):
        self.dismiss()
        self.app.push_screen("dashboard")

class ArmyApp(App):
    CSS = """
    Screen { background: #1a1a2e; }
    Header { background: #16213e; color: #e94560; }
    .panel { border: solid #e94560; padding: 1; margin: 1; background: #0f3460; color: #ffffff; }
    .button-panel { border: solid #533483; padding: 1; margin: 1; background: #0f3460; overflow-y: auto; max-height: 100%; }
    Button { margin: 1; }
    Input { margin: 1; background: #1a1a2e; color: #ffffff; }
    Label { margin: 1; color: #e94560; }
    TextArea { margin: 1; background: #1a1a2e; color: #ffffff; height: 10; }
    Footer { background: #16213e; color: #e94560; }
    """
    SCREENS = {"splash": SplashScreen, "dashboard": DashboardScreen}
    def on_mount(self): self.push_screen("splash")

if __name__ == "__main__":
    ArmyApp().run()
