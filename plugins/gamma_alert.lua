-- Если состояние гамма, выдаём рекомендацию
function on_state(state, delta)
  if state <= 2 then
    return "PANIC: немедленный recovery, не пиши Тошке"
  elseif state <= 3 then
    return "RECOVERY: подыши, отдохни"
  elseif delta == "delta" and state <= 5 then
    return "ОСТОРОЖНО: дельта активна, риск сорваться"
  end
  return nil
end
