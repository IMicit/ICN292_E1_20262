-- @titulo: Materiales por comprar antes de la próxima visita
-- @pregunta: ¿Qué hay que comprar, para qué local, y qué está deteniendo un tablero?
-- @interpretacion: Ésta es la consulta que convierte el RF-11 en algo útil. Que
--   el técnico registre el faltante no evita por sí solo el re-trabajo: lo evita
--   que abastecimiento vea la lista agrupada antes de volver al local.
--   La columna «accion» es la que importa y tiene tres valores con significados
--   distintos. «Comprar ahora» es un material que dejó un tablero sin poder
--   mantenerse, de modo que la cobertura del próximo ciclo depende de esa compra.
--   «Se repite» es el hallazgo que el papel nunca pudo mostrar: un consumible que
--   falta en varias visitas no es un olvido puntual, es un error de stock
--   permanente de la camioneta, y la decisión correcta no es comprarlo otra vez
--   sino subirlo al inventario base.
--   «veces_bloqueante» ordena el resultado a propósito: lo primero que aparece
--   es lo que está costando cobertura, y no lo que es más caro ni lo que se pidió
--   más veces.
--   La relación con la consulta 2 es directa. Un tablero que acumula ciclos sin
--   intervención por falta de material aparece acá con nombre y cantidad. La
--   consulta 2 dice qué tablero está detenido; ésta dice qué hay que comprar para
--   soltarlo.

WITH faltante AS (
    SELECT
        mf.descripcion,
        mf.cantidad,
        mf.unidad,
        mf.urgencia,
        l.nombre   AS local,
        c.periodo  AS ciclo,
        t.codigo   AS tablero
    FROM material_faltante mf
    JOIN visita  v ON v.id = mf.visita_id
    JOIN local   l ON l.id = v.local_id
    JOIN ciclo   c ON c.id = v.ciclo_id
    -- LEFT JOIN y no JOIN: el tablero es opcional, y un faltante de consumo
    -- general del local tiene que aparecer igual en la lista de compras.
    LEFT JOIN tablero t ON t.id = mf.tablero_id
)
SELECT
    local,
    descripcion                                   AS material,
    sum(cantidad)                                 AS cantidad,
    unidad,
    count(*)                                      AS veces_pedido,
    count(*) FILTER (WHERE urgencia = 'BLOQUEA')  AS veces_bloqueante,
    max(ciclo)                                    AS ultimo_ciclo,
    coalesce(
        string_agg(DISTINCT tablero, ', ')
            FILTER (WHERE urgencia = 'BLOQUEA'),
        '—'
    )                                             AS tableros_detenidos,
    CASE
        WHEN count(*) FILTER (WHERE urgencia = 'BLOQUEA') > 0
            THEN 'Comprar ahora: hay un tablero detenido'
        WHEN count(*) > 1
            THEN 'Se repite: subir al stock permanente de la camioneta'
        ELSE 'Reponer antes del próximo ciclo'
    END                                           AS accion
FROM faltante
GROUP BY local, descripcion, unidad
ORDER BY veces_bloqueante DESC, veces_pedido DESC, local, material;
