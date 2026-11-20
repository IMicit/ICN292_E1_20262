-- @titulo: Cobertura de mantención por local y ciclo
-- @pregunta: De los tableros que había que revisar en cada local, ¿cuántos se revisaron de verdad?
-- @interpretacion: Es el indicador central del proyecto y el que hoy IMELSE no
--   puede calcular. El checklist en papel se llena una vez por visita y no dice
--   a cuántos tableros se refiere, de modo que una hoja marcada «sí» en todos
--   los puntos puede corresponder a ocho tableros o a cinco. Aquí el
--   denominador viene del catálogo y el numerador de los registros sellados,
--   así que el porcentaje es verificable.
--   Una fila con cobertura bajo el 100 % y la visita ya cerrada no es un error:
--   significa que los tableros faltantes quedaron declarados como pendientes
--   con su motivo, que es la única salida que el sistema permite. La columna
--   «pendientes» muestra cuántos.

SELECT
    c.anio,
    c.periodo                                                   AS ciclo,
    l.nombre                                                    AS local,
    v.fecha,
    v.estado,
    count(DISTINCT t.id)                                        AS tableros_esperados,
    count(DISTINCT rt.tablero_id) FILTER (WHERE rt.cerrado)     AS tableros_registrados,
    count(DISTINCT p.tablero_id)                                AS pendientes,
    round(
        100.0 * count(DISTINCT rt.tablero_id) FILTER (WHERE rt.cerrado)
        / nullif(count(DISTINCT t.id), 0)
    , 1)                                                        AS cobertura_pct
FROM visita v
JOIN ciclo  c ON c.id = v.ciclo_id
JOIN local  l ON l.id = v.local_id
LEFT JOIN tablero t
       ON t.local_id = l.id AND t.activo
LEFT JOIN registro_tablero rt
       ON rt.visita_id = v.id
LEFT JOIN pendiente p
       ON p.visita_id = v.id
GROUP BY c.anio, c.periodo, l.nombre, v.fecha, v.estado
ORDER BY c.anio, c.periodo, l.nombre;
