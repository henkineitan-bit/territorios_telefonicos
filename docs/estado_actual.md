# Estado actual del proyecto (actualizado desde el código)

> Este documento describe **lo que el código hace hoy**, a diferencia de
> `docs/recursos_origen/Gestor de Territorios Telefónicos.pdf`, que es el
> documento técnico original del MVP y que se mantiene **sin tocar** como
> referencia histórica de lo que se planeó al principio.
>
> Cosas que están acá y **no** estaban en el documento original quedan
> marcadas con 🆕. Sirve para tener claro, de un vistazo, en qué se apartó
> el desarrollo del plan inicial.

---

## 1. Estructura del proyecto

```text
Territorios Telefonicos/
├── app.py                   # Punto de entrada: crea la app y registra los blueprints
├── database.py               # Conexión a SQLite (get_connection)
├── schema.sql                 # DDL de las 5 tablas
├── requirements.txt
│
├── routes/                    # 🆕 Rutas separadas por entidad (antes vivían en app.py)
│   ├── territorios.py         # /, /territorio/<id>, asignar, finalizar, historial
│   ├── responsables.py        # /responsables y sus acciones
│   └── registros.py           # actualizar/nuevo registro, importar/exportar
│
├── exports/                    # 🆕 Antes era un solo exports.py, ahora es un paquete
│   ├── celdas.py               # Helpers para interpretar celdas de Excel
│   ├── paleta.py                # Colores/estilos compartidos para PDF y PNG
│   ├── importacion_excel.py     # Upsert de territorios + registros
│   ├── importacion_historial.py # 🆕 Upsert de asignaciones desde un Excel de historial
│   ├── exportacion_excel.py
│   ├── exportacion_pdf.py
│   └── exportacion_png.py
│
├── templates/
│   ├── base.html, index.html, territorio.html
│   ├── responsables.html
│   ├── historial.html
│   ├── importar_excel.html
│   └── importar_historial.html   # 🆕
│
├── static/
│   ├── css/style.css
│   └── js/territorios.js          # 🆕 Filtro/orden en tiempo real del listado
│
├── data/territorios.db            # Base real de producción
├── docs/
│   ├── recursos_origen/            # PDF original, Excels de origen, mapa de rutas viejo
│   ├── auditoria_historica.md      # Auditoría de una sesión anterior
│   └── estado_actual.md            # Este archivo
└── scripts/iniciar_app.bat
```

---

## 2. Mapa de rutas actual

| Método | Ruta | Qué hace | ¿Estaba en el doc original? |
|---|---|---|---|
| GET | `/` | Listado de territorios con estado, responsable y buscador | Sí |
| POST | `/territorios/nuevo` | Crea un territorio manualmente desde un modal | 🆕 No — el doc solo preveía crear territorios vía importación de Excel |
| GET | `/territorio/<id>` | Detalle con tabla de registros editable | Sí |
| GET | `/territorio/<id>/historial` | Cronología de asignaciones y actividad | Sí |
| POST | `/territorio/<id>/asignar` | Asigna a un responsable (bloquea si ya está "En trabajo") | Sí |
| POST | `/territorio/<id>/finalizar` | Cierra la asignación activa | Sí |
| POST | `/territorio/<id>/actualizar-registro` | Guarda observaciones/no_llamar/funcionan/notas_internas | Sí |
| POST | `/territorio/<id>/nuevo-registro` | Agrega un registro telefónico a mano | 🆕 No |
| GET/POST | `/responsables` | Listado y alta de responsables | Sí (alta y listado) |
| POST | `/responsables/<id>/editar` | Edita nombre/teléfono/email de un responsable | 🆕 No |
| POST | `/responsables/<id>/desactivar` | Desactiva (no borra) | Sí |
| POST | `/responsables/<id>/activar` | Reactiva | Implícito en el ABM del doc |
| POST | `/responsables/lote` | Acciones masivas (activar/desactivar varios a la vez) | 🆕 No |
| GET/POST | `/importar-excel` | Importa/actualiza territorios y registros desde Excel | Sí |
| GET/POST | `/importar-historial` | Importa asignaciones históricas desde Excel y sincroniza estado | Sí (sección 11 del doc) |
| GET | `/exportar/excel` | Exporta registros, completo o filtrado por territorio | Sí |
| GET | `/territorio/<id>/exportar/pdf` | PDF imprimible del territorio | Sí |
| GET | `/territorio/<id>/exportar/png` | PNG del territorio | Sí |

**Resumen:** de las 18 rutas actuales, 5 no estaban contempladas en el documento
original (creación manual de territorios/registros, edición y acciones en
lote de responsables). Ninguna rompe las reglas de negocio del MVP (la
protección contra doble-asignación sigue aplicando siempre), pero es
funcionalidad de más sobre la que vale la pena decidir conscientemente si
se mantiene o se recorta.

---

## 3. Esquema de base de datos actual

Las tablas `territorios`, `registros`, `asignaciones` y `actividad` son
**idénticas** al `ai_studio_code.sql` original. La única diferencia está en
`responsables`:

```sql
CREATE TABLE IF NOT EXISTS responsables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    activo INTEGER DEFAULT 1,
    telefono TEXT DEFAULT NULL,   -- 🆕 no estaba en el doc (sección 6.3)
    email TEXT DEFAULT NULL,       -- 🆕 no estaba en el doc
    fecha_alta TEXT DEFAULT NULL   -- 🆕 no estaba en el doc
);
```

El documento original solo pedía `id`, `nombre`, `activo` para esta tabla.

---

## 4. Problema conocido, todavía sin corregir

**Responsables duplicados por nombre.** `importacion_historial.py` busca al
responsable con `WHERE nombre = ?` (coincidencia exacta). Si el mismo
responsable aparece en el Excel con una tilde de más/menos o un typo
("Jorge Papatanasi" vs "Jorge Papatanasi**s**i"), se crea una fila nueva en
vez de reutilizar la existente. Ya estaba detectado en
`docs/auditoria_historica.md` y sigue presente en el código actual.

---

## 5. Dato de la base real (no es un bug de código)

Al momento de esta revisión, los 226 territorios de `data/territorios.db`
figuran todos como "En trabajo", porque el Excel de historial importado
tenía la columna "Fecha completado" vacía en todas las filas. Es un tema de
los datos de origen, no del código de importación.
