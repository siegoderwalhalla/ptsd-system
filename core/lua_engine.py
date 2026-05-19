import subprocess
import os

PLUGINS_DIR = os.path.expanduser("~/army_system_py/plugins")

def run_plugin(plugin_name, func_name, args):
    plugin_path = os.path.join(PLUGINS_DIR, plugin_name)
    if not os.path.exists(plugin_path):
        return None
    
    # Формируем аргументы как Lua-таблицу
    lua_args = ", ".join([f"'{a}'" if isinstance(a, str) else str(a) for a in args])
    
    # Код на Lua с явным выводом через io.write
    lua_lines = [
        f'dofile("{plugin_path}")',
        f'result = {func_name}({lua_args})',
        'if result ~= nil then',
        '    io.write(result)',
        'end'
    ]
    lua_code = "\n".join(lua_lines)
    
    try:
        result = subprocess.check_output(
            ["lua5.4", "-e", lua_code],
            timeout=2,
            stderr=subprocess.DEVNULL
        ).decode().strip()
        return result if result else None
    except subprocess.CalledProcessError:
        return None
    except Exception:
        return None

def on_trigger(trigger_code, state):
    return run_plugin("auto_delta.lua", "on_trigger", [trigger_code, state])

def on_state(state, delta):
    return run_plugin("gamma_alert.lua", "on_state", [state, delta])

if __name__ == "__main__":
    print("🧪 Тест Lua-плагинов")
    
    r1 = on_trigger("ТОШ", 4)
    print(f"   Триггер ТОШ при 4/10: {r1 or 'нет реакции'}")
    
    r2 = on_state(2, "none")
    print(f"   Гамма без дельты: {r2 or 'нет реакции'}")
    
    r3 = on_state(5, "delta")
    print(f"   Бета с дельтой: {r3 or 'нет реакции'}")
    
    r4 = on_trigger("ОБЩ", 5)
    print(f"   Триггер ОБЩ: {r4 or 'нет реакции'}")
