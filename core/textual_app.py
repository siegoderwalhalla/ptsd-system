"""
ARMY SYSTEM — финальное приложение на Textual.
Запуск: python ~/army_system_py/core/textual_app.py
Выход: Ctrl+Q или кнопка «Выход»
"""
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Button, Input, Label
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.screen import Screen
import sqlite3, os, subprocess, io, sys
from datetime import datetime, date

DB_PATH = os.path.expanduser("~/army_system_py/army.db")
ARMY_PY = os.path.expanduser("~/army_system_py/army.py")
CORE_DIR = os.path.expanduser("~/army_system_py/core")

def run_python_script(path):
    """Запускает Python-скрипт и возвращает его вывод"""
    old_stdout, sys.stdout = sys.stdout, io.StringIO()
    try:
        exec(open(path).read())
    except: pass
    result = sys.stdout.getvalue()
    sys.stdout = old_stdout
    return result

# ═══════════════════ ЭКРАН 1: ДАШБОРД ═══════════════════
class DashboardScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal():
            with Vertical(id="left"):
                with Container(classes="panel"):
                    yield Static(id="state_info")
                with Container(classes="panel"):
                    yield Static(id="stats_info")
                with Container(classes="panel"):
                    yield Static(id="graph_info")
            with Vertical(id="right"):
                with Container(classes="button-panel"):
                    yield Static("[bold reverse] НАВИГАЦИЯ [/]")
                    yield Button("📊 Записать состояние", id="btn_state", variant="primary")
                    yield Button("🔄 Recovery", id="btn_recovery")
                    yield Button("🚨 Panic", id="btn_panic", variant="error")
                    yield Button("🚪 Gate", id="btn_gate", variant="warning")
                    yield Button("📈 Анализ", id="btn_analyze")
                    yield Button("🔮 Прогноз", id="btn_predict")
                    yield Button("📋 Отчёт", id="btn_report")
                    yield Button("🔄 Обновить", id="btn_refresh")
                    yield Button("🚪 Выход", id="btn_exit", variant="error")
        yield Footer()

    def on_mount(self):
        self.refresh_dashboard()

    def refresh_dashboard(self):
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
            state_text = f"[bold]СОСТОЯНИЕ: {state}/10 — {level}{delta_str}[/bold]\n"
            state_text += f"Замер: {ts}\n"
            state_text += f"До ДМБ: {ddays} дней"
        else:
            state_text = "Нет данных"
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
                bar = "█" * bar_len
                emoji = "🟢" if val >= 7 else ("🟡" if val >= 4 else "🔴")
                graph_text += f"{day[-5:]}: {bar} {val} {emoji}\n"
        else:
            graph_text += "Нет данных"
        conn.close()
        self.query_one("#state_info", Static).update(state_text)
        self.query_one("#stats_info", Static).update(stats_text)
        self.query_one("#graph_info", Static).update(graph_text)

    def on_button_pressed(self, event: Button.Pressed):
        btn = event.button.id
        if btn == "btn_refresh": self.refresh_dashboard()
        elif btn == "btn_state": self.app.push_screen(StateScreen())
        elif btn == "btn_recovery": self.app.push_screen(RecoveryScreen())
        elif btn == "btn_panic": self.app.push_screen(PanicScreen())
        elif btn == "btn_gate": self.app.push_screen(GateScreen())
        elif btn == "btn_analyze": self.app.push_screen(AnalyzeScreen())
        elif btn == "btn_predict": self.app.push_screen(PredictScreen())
        elif btn == "btn_report": self.app.push_screen(ReportScreen())
        elif btn == "btn_exit": self.app.exit()

# ═══════════════════ ЭКРАН 2: ЗАПИСЬ СОСТОЯНИЯ ═══════════════════
class StateScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(classes="panel"):
            yield Static("[bold]📊 ЗАПИСЬ СОСТОЯНИЯ[/bold]\n")
            yield Label("Состояние (0-10):"); yield Input(placeholder="5", id="input_state")
            yield Label("Дельта? (y/n):"); yield Input(placeholder="n", id="input_delta")
            yield Label("Код триггера:"); yield Input(placeholder="ТОШ / _ ", id="input_code")
            yield Label("Комментарий:"); yield Input(placeholder="как ты?", id="input_comment")
            yield Button("✅ Сохранить", id="btn_save", variant="primary")
            yield Button("🔙 Назад", id="btn_back")
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

# ═══════════════════ ЭКРАНЫ 3-4: RECOVERY, PANIC ═══════════════════
class RecoveryScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(classes="panel"):
            yield Static("[bold]🔄 RECOVERY[/bold]\nДыхание: вдох 4 сек → выдох 6 сек. 6 циклов.\n")
            yield Label("Состояние после:"); yield Input(placeholder="6", id="rec_state")
            yield Label("Ощущения:"); yield Input(placeholder="стало легче", id="rec_comment")
            yield Button("✅ Сохранить", id="btn_rec_save", variant="primary")
            yield Button("🔙 Назад", id="btn_rec_back")
        yield Footer()
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn_rec_back": self.dismiss()
        elif event.button.id == "btn_rec_save":
            state = self.query_one("#rec_state", Input).value or "6"
            comment = self.query_one("#rec_comment", Input).value or ""
            subprocess.call(["python", ARMY_PY, "state", state, "RECOVERY", comment])
            self.dismiss()

class PanicScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(classes="panel"):
            yield Static("[bold]🚨 PANIC MODE[/bold]\nGrounding 5-4-3-2-1. Дыхание 4-4-6, 5 циклов.\n")
            yield Label("Состояние после:"); yield Input(placeholder="3", id="panic_state")
            yield Label("Ощущения:"); yield Input(placeholder="страх, дрожь", id="panic_comment")
            yield Button("✅ Сохранить", id="btn_panic_save", variant="error")
            yield Button("🔙 Назад", id="btn_panic_back")
        yield Footer()
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn_panic_back": self.dismiss()
        elif event.button.id == "btn_panic_save":
            state = self.query_one("#panic_state", Input).value or "3"
            comment = self.query_one("#panic_comment", Input).value or ""
            subprocess.call(["python", ARMY_PY, "state", state, "PANIC", comment])
            self.dismiss()

# ═══════════════════ ЭКРАН 5: GATE ═══════════════════
class GateScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(classes="panel"):
            yield Static("[bold]🚪 TOSHA GATE[/bold]\n")
            yield Static(id="gate_result"); yield Static("\n")
            yield Button("🔄 Обновить", id="btn_gate_refresh")
            yield Button("🔙 Назад", id="btn_gate_back")
        yield Footer()
    def on_mount(self): self.refresh_gate()
    def refresh_gate(self):
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("SELECT state, delta FROM states ORDER BY timestamp DESC LIMIT 1")
        row = c.fetchone(); text = ""
        if row:
            state, delta = row
            c.execute("SELECT COUNT(*) FROM triggers_log WHERE code='ТОШ' AND timestamp > datetime('now','-1 day')")
            tosh24 = c.fetchone()[0]
            block, reason = 0, ""
            if state <= 2: block, reason = 1, "КРИТИЧЕСКОЕ СОСТОЯНИЕ"
            elif state <= 3: block, reason = 1, "ТЯЖЁЛОЕ СОСТОЯНИЕ"
            elif delta == 'delta' and state <= 5: block, reason = 1, "ДЕЛЬТА АКТИВНА"
            elif tosh24 >= 3: block, reason = 1, "МНОГО ТРИГГЕРОВ ТОШ"
            elif state <= 4: block, reason = 2, "ПОНИЖЕННОЕ СОСТОЯНИЕ"
            elif state <= 5: block, reason = 2, "СРЕДНЕЕ СОСТОЯНИЕ"
            if block == 1: text = f"⛔ ДОСТУП ЗАБЛОКИРОВАН ({reason})\n\nНе пиши Тошке. Сделай recovery."
            elif block == 2: text = f"⚠️  ОГРАНИЧЕННЫЙ ДОСТУП ({reason})\n\nМожно коротко, без претензий."
            else: text = "✅ ДОСТУП РАЗРЕШЁН"
        else: text = "Нет данных"
        conn.close()
        self.query_one("#gate_result", Static).update(text)
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn_gate_back": self.dismiss()
        elif event.button.id == "btn_gate_refresh": self.refresh_gate()

# ═══════════════════ ЭКРАН 6: АНАЛИЗ ═══════════════════
class AnalyzeScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with ScrollableContainer(classes="panel"):
            yield Static("[bold]📈 АНАЛИЗАТОР ПАТТЕРНОВ[/bold]\n")
            yield Static(id="analyze_result")
        with Container(classes="button-panel"):
            yield Button("🔄 Обновить", id="btn_analyze_refresh")
            yield Button("🔙 Назад", id="btn_analyze_back")
        yield Footer()
    def on_mount(self): self.refresh_analyze()
    def refresh_analyze(self):
        result = run_python_script(os.path.join(CORE_DIR, "analyzer.py"))
        self.query_one("#analyze_result", Static).update(result[:2000])
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn_analyze_back": self.dismiss()
        elif event.button.id == "btn_analyze_refresh": self.refresh_analyze()

# ═══════════════════ ЭКРАН 7: ПРОГНОЗ ═══════════════════
class PredictScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(classes="panel"):
            yield Static("[bold]🔮 ПРЕДИКТОР[/bold]\n")
            yield Static(id="predict_result")
        with Container(classes="button-panel"):
            yield Button("🔄 Обновить", id="btn_predict_refresh")
            yield Button("🔙 Назад", id="btn_predict_back")
        yield Footer()
    def on_mount(self): self.refresh_predict()
    def refresh_predict(self):
        import sqlite3
        from datetime import datetime, timedelta
        from collections import defaultdict
        
        DB = os.path.expanduser("~/army_system_py/army.db")
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        
        out = []
        out.append("🔮 ПРЕДИКТОР СОСТОЯНИЙ")
        out.append("=" * 40)
        
        # Среднее по дням недели
        dow_avg = {}
        c.execute("""SELECT CAST(strftime('%w', timestamp) AS INTEGER), ROUND(AVG(state), 2), COUNT(*)
                     FROM states GROUP BY strftime('%w', timestamp)""")
        for dow, avg_s, cnt in c.fetchall():
            dow_avg[dow] = (avg_s, cnt)
        
        # Последние 3 дня
        c.execute("""SELECT DATE(timestamp), ROUND(AVG(state), 2)
                     FROM states GROUP BY DATE(timestamp) ORDER BY DATE(timestamp) DESC LIMIT 3""")
        recent = c.fetchall()
        
        # Тренд за неделю
        c.execute("""SELECT DATE(timestamp), ROUND(AVG(state), 2)
                     FROM states GROUP BY DATE(timestamp) ORDER BY DATE(timestamp) DESC LIMIT 7""")
        week = c.fetchall()
        
        # Последний триггер
        c.execute("""SELECT code, state FROM triggers_log ORDER BY timestamp DESC LIMIT 1""")
        last_trigger = c.fetchone()
        
        # Дельта
        c.execute("""SELECT COUNT(*) FROM states WHERE DATE(timestamp) = DATE('now') AND delta = 'delta'""")
        delta_active = c.fetchone()[0] > 0
        
        tomorrow_dow = (datetime.now() + timedelta(days=1)).weekday()
        sql_dow = (tomorrow_dow + 1) % 7
        dow_info = dow_avg.get(sql_dow, (None, 0))
        days_ru = ["Вс", "Пн", "Вт", "Ср", "Чт", "Пт", "Сб"]
        
        out.append(f"   Завтра: {days_ru[tomorrow_dow]}")
        if dow_info[1] > 0:
            out.append(f"   Среднее по этому дню: {dow_info[0]} ({dow_info[1]} замеров)")
        
        if recent:
            recent_avg = sum(r[1] for r in recent) / len(recent)
            out.append(f"   Среднее за 3 дня: {round(recent_avg, 2)}")
        
        if len(week) >= 2:
            trend = week[0][1] - week[-1][1]
            direction = "📈 РАСТЁТ" if trend > 0.5 else ("📉 ПАДАЕТ" if trend < -0.5 else "➖ СТАБИЛЬНО")
            out.append(f"   Тренд за неделю: {direction} ({round(trend, 2)})")
        
        if delta_active:
            out.append(f"   Δ Сегодня: АКТИВНА (риск выше)")
        
        if last_trigger:
            out.append(f"   Последний триггер: {last_trigger[0]} (состояние {last_trigger[1]})")
        
        out.append("")
        out.append("🔮 ПРЕДСКАЗАНИЕ:")
        
        score = 5.0
        reasons = []
        
        if dow_info[1] >= 3:
            dow_effect = dow_info[0] - 5.0
            score += dow_effect * 0.3
            reasons.append(f"день недели ({dow_info[0]:+.1f})")
        
        if len(week) >= 2 and abs(trend) > 0.3:
            score += trend * 0.5
            reasons.append(f"тренд ({trend:+.1f})")
        
        if recent:
            recent_effect = (recent_avg - 5.0) * 0.4
            score += recent_effect
            reasons.append(f"посл. дни ({recent_avg:+.1f})")
        
        if delta_active:
            score -= 1.5
            reasons.append("дельта (-1.5)")
        
        if last_trigger:
            if last_trigger[0] == 'ТОШ':
                score -= 1.0
                reasons.append("триггер ТОШ (-1.0)")
            elif last_trigger[0] in ('СМЕРТЬ', 'ИМП'):
                score -= 1.5
                reasons.append(f"тяжёлый триггер {last_trigger[0]} (-1.5)")
        
        score = round(max(1.0, min(10.0, score)), 1)
        levels = {8: "α", 7: "α⁺", 6: "β⁻", 5: "β", 4: "β⁺", 3: "γ⁻", 2: "γ", 1: "γ⁺"}
        level = levels.get(round(score), str(score))
        emoji = "🟢" if score >= 7 else ("🟡" if score >= 4 else "🔴")
        
        out.append(f"   Прогноз: {score}/10 — {level} {emoji}")
        if reasons:
            out.append(f"   Факторы: {', '.join(reasons)}")
        
        if score <= 3:
            out.append("   ⚠️  Высокий риск спада.")
        elif score <= 5:
            out.append("   💡 Средний уровень.")
        else:
            out.append("   ✅ Ожидается хороший день.")
        
        conn.close()
        self.query_one("#predict_result", Static).update("\n".join(out))
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn_predict_back": self.dismiss()
        elif event.button.id == "btn_predict_refresh": self.refresh_predict()

# ═══════════════════ ЭКРАН 8: ОТЧЁТ ═══════════════════
class ReportScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(classes="panel"):
            yield Static("[bold]📋 ОТЧЁТ ЗА МЕСЯЦ[/bold]\n")
            yield Label("Месяц (ГГГГ-ММ):")
            yield Input(placeholder=datetime.now().strftime("%Y-%m"), id="report_month")
            yield Static(id="report_result")
        with Container(classes="button-panel"):
            yield Button("📋 Показать", id="btn_report_show", variant="primary")
            yield Button("🔙 Назад", id="btn_report_back")
        yield Footer()
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn_report_back": self.dismiss()
        elif event.button.id == "btn_report_show":
            month = self.query_one("#report_month", Input).value or datetime.now().strftime("%Y-%m")
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
            result = sys.stdout.getvalue(); sys.stdout = old_stdout
            self.query_one("#report_result", Static).update(result)

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
    Footer { background: #16213e; color: #e94560; }
    """
    SCREENS = {"dashboard": DashboardScreen}
    def on_mount(self):
        self.push_screen("dashboard")

if __name__ == "__main__":
    ArmyApp().run()
