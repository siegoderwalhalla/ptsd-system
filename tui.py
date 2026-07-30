#!/usr/bin/env python3
"""
PTSD Monitor — TUI приложение.
Запуск: python tui.py
Выход: Ctrl+Q или кнопка «Выход»
"""
from core.tui_app import PTSDApp

if __name__ == "__main__":
    PTSDApp().run()
