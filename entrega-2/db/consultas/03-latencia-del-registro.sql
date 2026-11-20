-- @titulo: Latencia entre la ejecución en terreno y la disponibilidad en oficina
-- @pregunta: ¿Cuánto demora en llegar a la oficina lo que el técnico hizo en el local?
-- @interpretacion: El diagnóstico midió entre 16 y 24 horas de latencia con el
--   checklist en papel: la hoja viaja físicamente con la cuadrilla, alguien la
--   transcribe y recién entonces se arma el informe. Durante todo ese tiempo la
--   gerencia no sabe qué pasó en terreno.
--   Esta consulta mide lo mismo sobre el sistema. El resultado se cuenta en
--   minutos y no en horas, porque el cierre de la visita publica la evidencia
--   en el acto: no hay un paso de traspaso que eliminar, simplemente dejó de
--   existir. Es el número más contundente de la demostración, y conviene
--   presentarlo junto a la línea base de 16 a 24 horas para que se entienda la
--   magnitud del cambio.
--   La columna «minutos_captura_a_cierre» mide algo distinto y también útil:
--   cuánto dura la ejecución real de una visita, dato que hoy tampoco existe y
--   que sirve para planificar las rutas.

WITH jornada AS (
    SELECT
        rt.visita_id,
        min(rt.ts_inicio)  AS primer_tablero,
        max(rt.ts_cierre)  AS ultimo_tablero
    FROM registro_tablero rt
    WHERE rt.cerrado
    GROUP BY rt.visita_id
)
SELECT
    c.periodo                     AS ciclo,
    l.nombre                      AS local,
    v.fecha,
    j.primer_tablero,
    j.ultimo_tablero,
    v.ts_cierre,
    round(EXTRACT(EPOCH FROM (j.ultimo_tablero - j.primer_tablero)) / 60.0, 1)
                                  AS minutos_de_ejecucion,
    round(EXTRACT(EPOCH FROM (v.ts_cierre - j.ultimo_tablero)) / 60.0, 1)
                                  AS minutos_captura_a_cierre,
    -- Línea base del diagnóstico: 16 h en el mejor caso del proceso en papel.
    round(
        (16 * 60) - EXTRACT(EPOCH FROM (v.ts_cierre - j.ultimo_tablero)) / 60.0
    , 1)                          AS minutos_ahorrados_vs_papel
FROM visita v
JOIN jornada j ON j.visita_id = v.id
JOIN local   l ON l.id = v.local_id
JOIN ciclo   c ON c.id = v.ciclo_id
WHERE v.estado = 'CERRADA'
  AND v.ts_cierre IS NOT NULL
ORDER BY v.fecha;
