-- Если пришёл триггер ТОШ, автоматически включаем дельту
function on_trigger(code, state)
  if code == "ТОШ" then
    return "delta"
  end
  return nil
end
