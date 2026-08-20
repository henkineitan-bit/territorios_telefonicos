# 📞 Gestor de Territorios Telefónicos

Sistema web local desarrollado en **Flask (Python)** y **SQLite** para la gestión, asignación, seguimiento, exportación (PDF, PNG, Excel) e historial de territorios telefónicos.

---

## 🚀 Inicio Rápido

### En Windows (Doble Clic)
1. **Primera vez:** Ejecuta **`scripts\instalar.bat`** para crear el entorno virtual e instalar las dependencias.
2. **Siempre:** Ejecuta **`scripts\iniciar_app.bat`**. Se levantará el servidor Flask y se abrirá el navegador en `http://127.0.0.1:5000`.

> Si `iniciar_app.bat` detecta que no existe el entorno virtual, te pedirá que ejecutes `instalar.bat` primero.

### Desde la Terminal
1. Crea el entorno virtual e instala dependencias (solo la primera vez):
   ```bash
   python -m venv venv
   venv\Scripts\python.exe -m pip install -r requirements.txt
   ```
2. Ejecuta la aplicación:
   ```bash
   venv\Scripts\python.exe app.py
   ```
3. Visita en tu navegador: [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 📁 Estructura del Proyecto

```text
Territorios Telefonicos/
├── app.py                  # Punto de entrada compatible (usa create_app)
├── app/                    # Arquitectura desacoplada
│   ├── __init__.py         # Application Factory y registro de Blueprints
│   ├── config.py           # Configuración por entorno
│   ├── db.py               # Conexión, transacciones y migraciones numeradas
│   ├── blueprints/         # Controladores HTTP
│   ├── services/           # Reglas de negocio y casos de uso
│   └── repositories/       # Consultas SQL aisladas
├── database.py             # Fachada temporal de compatibilidad para app.db
├── schema.sql              # Esquema DDL de las tablas SQL
├── exports/                # Importación y exportación de archivos
├── legacy_exports.py       # Implementación anterior conservada como referencia
├── territorios.db          # Base de datos SQLite activa
├── requirements.txt        # Librerías de Python requeridas
│
├── templates/              # Vistas HTML (motor Jinja2)
│   ├── base.html           # Layout base compartido
│   ├── index.html          # Listado y filtros de territorios
│   ├── territorio.html     # Detalle, asignación y registro de números
│   ├── historial.html      # Historial global de asignaciones
│   ├── responsables.html   # Gestión de publicadores/responsables
│   ├── importar_excel.html # Importador de números desde Excel
│   └── importar_historial.html # Importador de historial
│
├── static/                 # Recursos estáticos
│   └── css/
│       └── style.css       # Estilos CSS
│
├── recursos_origen/        # Documentación de referencia, PDFs y Excels originales
│   ├── Gestor de Territorios Telefónicos.pdf
│   ├── Telefónico v2 (1).xlsx
│   ├── Registros Territorio telefónico.xlsx
│   └── Mapa de Rutas de Flask (Endpoints).txt
│
├── _historico_versiones/   # Respaldo de versiones previas (v1 - v8)
├── .gitignore              # Configuración de exclusión para Git
├── iniciar_app.bat         # Acceso directo para iniciar en Windows
├── como abrirlo.txt        # Guía rápida en texto plano
└── README.md               # Esta documentación
```

---

## ⚙️ Tecnologías Utilizadas

- **Backend:** Python 3 + [Flask 3](https://flask.palletsprojects.com/)
- **Base de Datos:** SQLite 3
- **Exportaciones:**
  - `reportlab`: Generación de planillas de territorio en PDF
  - `Pillow` (PIL): Generación de listas de números en imagen PNG
  - `openpyxl` / `pandas`: Exportación e importación de archivos Excel
- **Frontend:** HTML5 semántico, CSS responsivo y plantillas Jinja2
