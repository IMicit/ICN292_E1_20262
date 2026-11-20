-- @titulo: Motivos por los que un tablero queda sin intervenir
-- @pregunta: ¿Qué impide completar las visitas, y es un problema del local o de la planificación?
-- @interpretacion: Con el papel, un tablero no intervenido simplemente no
--   aparecía: quedaba un casillero en blanco que nadie podía interpretar
--   después. El sistema obliga a declarar el motivo desde una lista cerrada, y
--   eso convierte el silencio en información agregable.
--   La lectura es directa. Si predomina «sala sin acceso», el problema es de
--   coordinación con el local y se resuelve avisando antes de ir. Si predomina
--   «tiempo insuficiente», el problema es de planificación de rutas y se
--   resuelve asignando menos locales por jornada. Si predomina «falta de
--   material», el problema está en bodega y conecta con la manifestación P6 del
--   diagnóstico.
--   Son decisiones distintas, y hoy no hay forma de saber cuál tomar.

SELECT
    l.nombre                                             AS local,
    p.motivo,
    count(*)                                             AS veces,
    count(DISTINCT p.tablero_id)                         AS tableros_distintos,
    count(DISTINCT v.ciclo_id)                           AS ciclos_afectados,
    round(100.0 * count(*) / sum(count(*)) OVER (PARTITION BY l.nombre), 1)
                                                         AS pct_del_local,
    min(v.fecha)                                         AS primera_vez,
    max(v.fecha)                                         AS ultima_vez
FROM pendiente p
JOIN visita v ON v.id = p.visita_id
JOIN local  l ON l.id = v.local_id
GROUP BY l.nombre, p.motivo
ORDER BY l.nombre, veces DESC;
