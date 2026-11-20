-- @titulo: Puntos de la pauta que más veces resultan no conformes
-- @pregunta: ¿Qué componentes fallan más seguido, y en qué locales se concentran?
-- @interpretacion: El sistema no sólo registra que la pauta se cumplió: registra
--   el resultado de cada punto por separado, y eso permite agregar algo que el
--   papel nunca permitió. Si el reapriete de borneras aparece como no conforme
--   en el 30 % de los tableros de un local, eso no es un problema de la
--   cuadrilla: es un problema de la instalación de ese local, y conviene
--   plantearlo al cliente antes de que algo falle.
--   La columna «sin_evidencia» es un control de calidad del propio registro, no
--   del cliente. Debería ser siempre cero, porque el sistema no permite sellar
--   un tablero con ítems declarados ejecutados sin fotografía vinculada (RF-03).
--   Si alguna vez saliera distinta de cero, significaría que la regla se rompió
--   y habría que revisar por dónde.
--   Se consideran sólo las respuestas vigentes: una respuesta corregida sigue
--   en la tabla pero no se cuenta dos veces.

WITH vigentes AS (
    SELECT ri.*
    FROM registro_item ri
    WHERE NOT EXISTS (
        SELECT 1 FROM registro_item c WHERE c.corrige_a_id = ri.id
    )
),
con_foto AS (
    SELECT DISTINCT ri.id
    FROM vigentes ri
    JOIN evidencia e        ON e.registro_tablero_id = ri.registro_tablero_id
    JOIN evidencia_item ei  ON ei.evidencia_id = e.id
                           AND ei.itemchecklist_id = ri.item_id
)
SELECT
    s.numero || '.' || i.orden                                  AS codigo,
    i.descripcion,
    i.ambito,
    count(*)                                                    AS respuestas,
    count(*) FILTER (WHERE v.resultado = 'NO')                  AS no_conformes,
    count(*) FILTER (WHERE v.resultado = 'NA')                  AS no_aplica,
    round(100.0 * count(*) FILTER (WHERE v.resultado = 'NO') / nullif(count(*), 0), 1)
                                                                AS pct_no_conforme,
    count(*) FILTER (
        WHERE v.resultado = 'SI'
          AND v.registro_tablero_id IS NOT NULL
          AND v.id NOT IN (SELECT id FROM con_foto)
    )                                                           AS sin_evidencia,
    count(DISTINCT l.id) FILTER (WHERE v.resultado = 'NO')      AS locales_afectados
FROM vigentes v
JOIN item_checklist    i ON i.id = v.item_id
JOIN seccion_checklist s ON s.id = i.seccion_id
JOIN visita           vi ON vi.id = v.visita_id
JOIN local             l ON l.id = vi.local_id
GROUP BY s.numero, i.orden, i.descripcion, i.ambito
HAVING count(*) FILTER (WHERE v.resultado = 'NO') > 0
ORDER BY pct_no_conforme DESC, no_conformes DESC;
