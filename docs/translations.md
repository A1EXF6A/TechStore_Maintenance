# TechStore Mantenimiento - Traducciones y Localización

Este documento describe la arquitectura para la internacionalización (i18n) del módulo, el script automatizado para traducciones basado en diccionarios y los pasos para dar soporte a nuevos términos de idioma.

---

## 1. Estructura de Directorios i18n en Odoo

Las localizaciones del addon se almacenan en el subdirectorio `i18n` dentro de la carpeta del módulo:
* **Ruta de Traducciones:** `addons/techstore_maintenance/i18n/`
* **Archivos Principales:**
  * `techstore_maintenance.pot`: La Plantilla de Traducciones (POT) exportada por Odoo que contiene todos los términos originales en inglés (`msgid`).
  * `es.po`: El archivo de traducciones al español (PO) que contiene las cadenas traducidas finalizadas (`msgstr`).

---

## 2. Script Automatizado de Traducción

Para acelerar la traducción de nuevos campos y etiquetas en la interfaz, el proyecto incluye un utilitario automatizado en Python: [translate.py](file:///d:/universidad/septimo/GCS/TechStore_Maintenance/translate.py).

### Mecánica de Funcionamiento:
1. **Diccionario de mapeos:** El script cuenta con un diccionario de traducción estático `translations` que mapea cadenas en inglés a su equivalente en español.
2. **Lectura de plantilla:** Carga el archivo de plantilla `techstore_maintenance.pot` y procesa el texto:
   * Identifica bloques que inician con `msgid "Texto en Inglés"` seguidos por la cadena vacía de traducción `msgstr ""`.
   * Si `Texto en Inglés` coincide con alguna clave registrada en el diccionario del script, reemplaza la línea vacía por la cadena traducida:
     ```text
     msgstr "Texto en Español"
     ```
3. **Escritura del archivo final:** Escribe el resultado procesado en el archivo de localización [es.po](file:///d:/universidad/septimo/GCS/TechStore_Maintenance/addons/techstore_maintenance/i18n/es.po), respetando el formato estándar de Odoo.

---

## 3. Guía Paso a Paso para Actualizar Cadenas de Idioma

Cuando añada nuevas vistas, modelos, campos o mensajes de error, siga este procedimiento para actualizar la localización en español:

### Paso 1: Exportar la Plantilla POT desde Odoo
Con el **Modo Desarrollador** activo en la interfaz de Odoo:
1. Vaya a **Ajustes** $\to$ **Traducciones** $\to$ **Exportar Traducciones**.
2. Complete la configuración:
   * **Idioma:** `Spanish (EC) / Español (EC)` (o la localización en español que use).
   * **Formato:** `Archivo PO`
   * **Aplicación:** `TechStore Mantenimiento`
3. Haga clic en **Exportar** y descargue el archivo.
4. Renombre el archivo descargado a `techstore_maintenance.pot` y colóquelo en el directorio de i18n del módulo:
   [addons/techstore_maintenance/i18n/techstore_maintenance.pot](file:///d:/universidad/septimo/GCS/TechStore_Maintenance/addons/techstore_maintenance/i18n/techstore_maintenance.pot)

### Paso 2: Registrar Cadenas Nuevas en el Diccionario
Abra [translate.py](file:///d:/universidad/septimo/GCS/TechStore_Maintenance/translate.py) y agregue las nuevas cadenas en inglés y su respectiva traducción al diccionario `translations`:
```python
translations = {
    # ... cadenas existentes
    "My New Label": "Mi Nueva Etiqueta",
}
```

### Paso 3: Ejecutar el Script de Traducción
Desde la consola en el directorio raíz de la aplicación, corra el script utilitario:
```bash
python translate.py
```
Este comando reescribirá el archivo [es.po](file:///d:/universidad/septimo/GCS/TechStore_Maintenance/addons/techstore_maintenance/i18n/es.po) agregando las traducciones encontradas en el diccionario.

### Paso 4: Cargar las Cadenas Actualizadas en Odoo
Para importar los cambios en la base de datos de desarrollo, force la actualización del módulo:
* **Vía Consola (Docker):**
  ```bash
  docker-compose exec odoo odoo -c /etc/odoo/odoo.conf -d odoo_db -u techstore_maintenance --stop-after-init
  ```
* **Vía Interfaz Web:** Vaya al panel de **Aplicaciones**, busque `TechStore Mantenimiento` y haga clic en **Actualizar**. Odoo cargará automáticamente el contenido del archivo `es.po` al detectar la actualización.
