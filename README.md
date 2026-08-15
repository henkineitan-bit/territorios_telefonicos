# 📞 Gestor de Territorios Telefónicos

Sistema web local desarrollado en **Flask (Python)** y **SQLite** para la gestión, asignación, seguimiento, exportación (PDF, PNG, Excel) e historial de territorios telefónicos.

---

## 🚀 Inicio Rápido

### En Windows (Doble Clic)
Simplemente ejecuta el archivo **`iniciar_app.bat`**. Se levantará el servidor Flask y se abrirá el navegador en `http://127.0.0.1:5000`.

### Desde la Terminal
1. Asegúrate de tener las dependencias instaladas:
   ```bash
   pip install -r requirements.txt
   ```
2. Ejecuta la aplicación:
   ```bash
   python app.py
   ```
3. Visita en tu navegador: [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 📁 Estructura del Proyecto

```text
Territorios Telefonicos/
├── app.py                  # Servidor Flask principal y definición de endpoints
├── database.py             # Helpers y conexión a SQLite
├── exports.py              # Exportaciones a PDF (ReportLab), PNG (Pillow) y Excel (openpyxl)
├── schema.sql              # Esquema DDL de las tablas SQL
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
