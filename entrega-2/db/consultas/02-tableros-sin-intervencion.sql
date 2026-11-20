-- @titulo: Tableros que acumulan ciclos sin intervención
-- @pregunta: ¿Qué tableros llevan más tiempo sin que nadie los revise, y por qué?
-- @interpretacion: Ésta es la consulta que justifica el proyecto completo. El
--   diagnóstico de la Entrega 1 decía que hay tableros que pasan ciclos
--   bimensuales enteros sin revisión y que nadie se entera hasta que fallan.
--   Con el papel esa afirmación no se podía comprobar. Acá se ve.
--   La columna «meses_sin_intervencion» es la que importa para la gerencia: un
--   tablero con cinco ciclos pendientes lleva diez meses descubierto, y cuando
--   falle la visita de emergencia la paga IMELSE por contrato. El motivo
--   recurrente indica además si el problema es operativo —una sala cuya llave
--   nadie tiene— o de planificación.

WITH ultima_intervencion AS (
    SELECT rt.tablero_id,
           max(v.fecha) AS fecha_ultima,
           count(*)     AS veces_intervenido
    FROM registro_tablero rt
    JOIN visita v ON v.id = rt.visita_id
    WHERE rt.cerrado
    GROUP BY rt.tablero_id
),
pendientes_por_tablero AS (
    SELECT p.tablero_id,
           count(*)                                   AS ciclos_pendiente,
           mode() WITHIN GROUP (ORDER BY p.motivo)     AS motivo_recurrente
    FROM pendiente p
    GROUP BY p.tablero_id
)
SELECT
    l.nombre                                   AS local,
    t.codigo                                   AS tablero,
    t.ubicacion,
    t.tipo,
    coalesce(u.veces_intervenido, 0)           AS veces_intervenido,
    u.fecha_ultima                             AS ultima_intervencion,
    coalesce(pp.ciclos_pendiente, 0)           AS ciclos_pendiente,
    pp.motivo_recurrente,
    -- Restar dos fechas en PostgreSQL devuelve días enteros, no un intervalo.
    CASE
        WHEN u.fecha_ultima IS NULL THEN NULL
        ELSE round((CURRENT_DATE - u.fecha_ultima) / 30.0, 1)
    END                                        AS meses_sin_intervencion
FROM tablero t
JOIN local l                      ON l.id  = t.local_id
LEFT JOIN ultima_intervencion u   ON u.tablero_id = t.id
LEFT JOIN pendientes_por_tablero pp ON pp.tablero_id = t.id
WHERE t.activo
  AND coalesce(pp.ciclos_pendiente, 0) > 0
ORDER BY pp.ciclos_pendiente DESC NULLS LAST, meses_sin_intervencion DESC NULLS FIRST;
