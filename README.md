# TechStore Mantenimiento - Módulo de Odoo 18

Bienvenido al portal de documentación para desarrolladores de **TechStore Mantenimiento**, un módulo personalizado de Odoo 18 diseñado para gestionar flujos de trabajo de mantenimientos técnicos, carga de trabajo de los técnicos, recepción y ciclo de vida de los equipos, y métricas de nivel de servicio (SLA).

---

## 📖 Índice de Documentación para Desarrolladores

Para profundizar en las especificaciones técnicas de cada componente, explore las guías detalladas a continuación:

* 📐 **[Arquitectura Técnica y Máquina de Estados](file:///d:/universidad/septimo/GCS/TechStore_Maintenance/docs/architecture.md)**
  *Modelos lógicos, relaciones de base de datos, máquina de estados del ciclo de vida, integraciones de wizards para comentarios y el patch JS personalizado para el controlador de drag-and-drop en el Kanban.*
* 🔒 **[Roles, Reglas de Acceso y Seguridad](file:///d:/universidad/septimo/GCS/TechStore_Maintenance/docs/roles_permissions.md)**
  *Jerarquía de grupos de seguridad (Técnico, Supervisor, Administrador), Listas de Control de Acceso (ACL CSV), reglas de registro para aislamiento y guardias de validación de Python/XML.*
* 🛡️ **[Validaciones de Datos y Lógica de Negocio](file:///d:/universidad/septimo/GCS/TechStore_Maintenance/docs/validation_business_logic.md)**
  *Algoritmo de validación de módulo 10 para la cédula ecuatoriana, formato de números telefónicos, campos requeridos para finalizar tickets y sincronización automática de estados de equipos.*
* 📊 **[Métricas de Telemetría y Motor de Reportes](file:///d:/universidad/septimo/GCS/TechStore_Maintenance/docs/reports_metrics.md)**
  *Fórmulas matemáticas para los cálculos de SLA, indicador de satisfacción del cliente, plantillas PDF de QWeb y el wizard para generación de Excel multi-pestaña mediante `xlsxwriter`.*
* 🧪 **[Guía del Framework de Pruebas Unitarias](file:///d:/universidad/septimo/GCS/TechStore_Maintenance/docs/testing.md)**
  *Cobertura de la suite de pruebas unitarias (25 casos de prueba automatizados), configuración de entornos mock y comandos de terminal para ejecutar los tests dentro de contenedores Docker.*
* 🌐 **[Traducciones y Localización](file:///d:/universidad/septimo/GCS/TechStore_Maintenance/docs/translations.md)**
  *Directorios de i18n de Odoo, plantillas PO/POT y el script de utilidad para traducciones automáticas basado en diccionarios (`translate.py`).*

---

## 🚀 Inicio Rápido (Entorno Docker)

El repositorio incluye un stack de contenedores Docker preconfigurado con **Odoo 18** y **PostgreSQL 15**.

### 1. Iniciar los contenedores
Ejecute el siguiente comando desde el directorio raíz del proyecto:
```bash
docker-compose up -d
```

### 2. Verificar el mapeo de puertos
* **Interfaz web de Odoo:** [http://localhost:8069](http://localhost:8069)
* **Puerto de PostgreSQL:** `5432` (accesible internamente dentro de la red Docker)

---

## 🛠️ Detalles de Configuración

Los archivos de configuración se encuentran en el directorio [config/](file:///d:/universidad/septimo/GCS/TechStore_Maintenance/config):
* **Archivo de configuración:** [config/odoo.conf](file:///d:/universidad/septimo/GCS/TechStore_Maintenance/config/odoo.conf)
* **Parámetros clave:**
  * `admin_passwd`: Contraseña maestra para la gestión de bases de datos.
  * `db_host`: Mapeado a `db` (nombre del servicio Postgres en la red Docker).
  * `db_user` / `db_password`: Configurados como `odoo` / `odoo`.
  * `addons_path`: Configurado para incluir `/mnt/extra-addons` (que monta el directorio local `./addons`).

---

## 📦 Cómo instalar y actualizar el módulo

### Instalación:
1. Inicie sesión en Odoo en `http://localhost:8069` usando las credenciales de administrador.
2. Vaya a **Ajustes** $\to$ **Ajustes Generales** y active el **Modo Desarrollador**.
3. Diríjase a **Aplicaciones** $\to$ haga clic en **Actualizar lista de aplicaciones** en el menú superior.
4. Busque `TechStore Mantenimiento` (nombre técnico: `techstore_maintenance`).
5. Haga clic en **Activar**.

### Actualización rápida (Línea de comandos):
Si modificó código Python o vistas XML, puede forzar la actualización del módulo sin usar el navegador:
```bash
docker-compose exec odoo odoo -c /etc/odoo/odoo.conf -d odoo_db -u techstore_maintenance --stop-after-init
```

---

## 💡 Preguntas Frecuentes y Resolución de Problemas

#### ¿Por qué no se muestran mis cambios de Python en la UI?
A diferencia de JavaScript, Odoo carga y compila los modelos de Python en memoria al iniciar. **Debe reiniciar** el contenedor Docker de Odoo y actualizar el módulo para aplicar los cambios:
```bash
docker-compose restart odoo
docker-compose exec odoo odoo -c /etc/odoo/odoo.conf -d odoo_db -u techstore_maintenance --stop-after-init
```

#### ¿Por qué el reporte PDF se imprime sin estilos CSS?
El generador de PDF QWeb de Odoo utiliza la herramienta externa `wkhtmltopdf`. Esta requiere descargar los recursos CSS del servidor mediante enlaces absolutos. Asegúrese de que el parámetro del sistema `web.base.url` en Odoo esté configurado exactamente como `http://localhost:8069` (o la URL de su servidor).

#### ¿Cómo vuelvo a cargar los datos de prueba?
Los datos iniciales se cargan automáticamente desde los archivos CSV en `addons/techstore_maintenance/data/` al instalar el módulo. Si desea volver a cargarlos, reconstruya la base de datos o ejecute:
```bash
docker-compose exec odoo odoo -c /etc/odoo/odoo.conf -d odoo_db -i techstore_maintenance --init
```
