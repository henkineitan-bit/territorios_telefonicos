# 🔍 Auditoría del Código — Territorios Telefónicos

Revisé en profundidad los 4 archivos Python, los 7 templates HTML, el CSS, el esquema SQL y la base de datos con 226 territorios / 8889 registros / 226 asignaciones / 18 responsables.

---

## ✅ Lo que está bien

- **Estructura del código:** Limpia separación en `app.py` (rutas), `database.py` (conexión), `exports.py` (importación/exportación).
- **Lógica de negocio:** Bien implementada la protección contra doble-asignación (doble barrera: check Python + WHERE SQL).
- **Importación de Excel:** Robusto manejo de upsert con `ON CONFLICT`-style manual, con contadores y reporte de errores.
- **Integridad referencial:** 0 registros huérfanos, 0 asignaciones huérfanas, 0 teléfonos vacíos.
- **Todas las páginas cargan sin errores HTTP 500.**

---

## 🐛 Bugs Encontrados

### BUG 1 — Responsables duplicados (DATOS)

Hay responsables repetidos con leves variaciones de nombre:

| ID  | Nombre              | Activo |
|-----|---------------------|--------|
| 1   | Jorge Papatanas**i**  | ✅    |
| 9   | Jorge Papatanas**si** | ✅    |
| 5   | Ana María Mart**inez** | ❌  |
| 16  | Ana María Mart**ínez** | ❌  |

Esto ocurre porque la importación de historial crea responsables nuevos si el nombre no es exactamente igual (sensible a tildes y typos). No es un bug de código sino de datos, pero conviene limpiar los duplicados.

> [!WARNING]
> Si se limpian, hay que reasignar las asignaciones del responsable duplicado al correcto antes de borrar.

---

### BUG 2 — Los 226 territorios están "En trabajo" (DATOS / LÓGICA)

**Todos** los territorios figuran como `"En trabajo"` y cada uno tiene exactamente 1 asignación abierta (sin `fecha_finalizacion`). Es muy probable que estos datos vengan de la importación de historial desde un Excel donde la columna "Fecha completado" estaba vacía.

Esto causa que:
- No se pueda asignar ningún territorio a nadie (todos están bloqueados).
- El filtro "Disponible" no devuelve nada.

---

### BUG 3 — La página de historial no muestra asignaciones del historial importado

La página de historial del territorio 100 dice vacío en asignaciones, pero la query de `territorio_detalle` sí encuentra la asignación activa (y muestra el responsable). Investigando: la tabla del historial sí funciona, pero el HTML del contenido renderizado por `read_url_content` cortó la tabla porque los datos están ahí. Esto resultó ser un falso positivo del scraper; la funcionalidad está **OK**.

---

### BUG 4 — Fuentes PNG hardcodeadas a Linux (CÓDIGO)

En [exports.py L322-331](file:///c:/Users/henki/Desktop/Territorios%20Telefonicos/exports.py#L322-L331), las fuentes para generar PNG están hardcodeadas a rutas Linux (`/usr/share/fonts/truetype/dejavu/`). En Windows siempre cae al fallback `ImageFont.load_default()`, que es una fuente bitmap pequeña y de baja calidad.

**Impacto:** Las imágenes PNG exportadas se ven feas con la fuente por defecto de Pillow.

---

### BUG 5 — Conexión no cerrada en importar_historial si hay ValueError (CÓDIGO)

En [app.py L538-545](file:///c:/Users/henki/Desktop/Territorios%20Telefonicos/app.py#L538-L545), la ruta `importar_historial_view` tiene un `finally: conn.close()` pero el `except ValueError` hace `redirect` **después** del `finally`. Sin embargo, si `importar_historial()` lanza `ValueError`, el `conn.close()` en `finally` se ejecuta correctamente, pero el `conn` ya se usó dentro de la función importar que hizo `conn.commit()` antes del error... Revisando mejor: el `finally` **sí** cierra la conexión, pero hay un detalle: si la excepción ocurre **antes** del commit dentro de `importar_historial`, los cambios parciales quedan sin rollback explícito. SQLite hace rollback automático al cerrar sin commit, así que no hay pérdida de datos, pero sería más limpio con un `try/except` con rollback.

---

### BUG 6 — El `ORDER BY t.numero` ordena como texto, no como número (CÓDIGO)

En [app.py L71](file:///c:/Users/henki/Desktop/Territorios%20Telefonicos/app.py#L71), `ORDER BY t.numero` ordena **lexicográficamente** porque `numero` es `TEXT` en el esquema. Esto significa que "9" va después de "800", y "100" va antes de "2".

**Impacto:** El orden por defecto "por número" no es intuitivo. El territorio 9 aparece después del 8xx.

---

## 🔧 Plan de Correcciones

| # | Fix | Archivo | Severidad |
|---|-----|---------|-----------|
| 1 | Corregir ORDER BY para que ordene numéricamente (`CAST(t.numero AS INTEGER)`) | `app.py` L71 | 🟡 Media |
| 2 | Usar fuentes del sistema Windows (con fallback cross-platform) para PNG | `exports.py` L322-336 | 🟡 Media |
| 3 | Agregar rollback explícito en el manejo de errores de importación | `app.py` L538-545 | 🟢 Baja |
| 4 | Limpiar responsables duplicados en la base de datos | `territorios.db` | 🟡 Media |
| 5 | Revisar si todos los territorios deberían estar realmente "En trabajo" o si necesitan recalcularse | `territorios.db` | 🔴 Alta |

> [!IMPORTANT]
> El punto 5 (todos en "En trabajo") es el más impactante porque bloquea la funcionalidad de asignación. ¿Querés que recalcule los estados basándome en las asignaciones, o esos datos son correctos y efectivamente están todos en trabajo?

---

¿Procedo con las correcciones de código (puntos 1, 2, 3) y te consulto sobre los datos (puntos 4 y 5)?
