# TechStore Mantenimiento - Guía de Pruebas Unitarias

Este documento detalla la infraestructura del suite de pruebas, la lista detallada de los 25 casos de prueba unitaria y las instrucciones para ejecutar las pruebas en el entorno local de desarrollo.

---

## 1. Framework de Pruebas

El módulo utiliza el suite de pruebas nativo de Odoo, construido sobre la biblioteca estándar `unittest` de Python.
* **Clase de Pruebas:** `TestTechStoreMaintenance` hereda de `odoo.tests.common.TransactionCase`.
* **Archivo de Pruebas:** [test_maintenance.py](file:///d:/universidad/septimo/GCS/TechStore_Maintenance/addons/techstore_maintenance/tests/test_maintenance.py)
* **Aislamiento de Entorno:** Las pruebas se ejecutan en transacciones de base de datos aisladas que se revierten automáticamente al finalizar cada método de test (`rollback`), garantizando que no queden datos residuales.

---

## 2. Configuración de Datos de Prueba (`setUpClass`)

En el método de clase `setUpClass()`, se genera una estructura base de datos simulada compartida por todos los tests:
* **Especialidad:** Registra una especialidad técnica llamada "Hardware Test".
* **Cliente:** Registra un cliente de prueba "Test Client S.A." con RUC `1792345678009`.
* **Equipo:** Registra una computadora portátil "Dell Latitude" con número de serie `SN-TEST-123` en estado físico `received` (Ingresado).
* **Técnico:** Registra un técnico de prueba "Test Tech" con cédula ecuatoriana válida `1708932452` y teléfono válido `0999999991`.
* **Usuario Técnico:** Registra un usuario de Odoo `tech_user` asignado al grupo de seguridad de Técnicos y lo vincula con el perfil de técnico recién creado.

---

## 3. Catálogo de los 25 Casos de Prueba

La suite de pruebas cubre validaciones del modelo, restricciones de negocio, flujos del ciclo de vida y reglas de seguridad de datos:

### Pruebas de Registro de Técnicos
1. **`test_01_technician_validation_valid`**: Valida que la creación de un técnico con una cédula válida (según algoritmo de módulo 10) y un número de teléfono de 10 dígitos se procese de manera exitosa.
2. **`test_01_technician_validation_invalid_cedula`**: Verifica que intentar registrar un técnico con una cédula de identidad inválida (que falla en la suma ponderada del módulo 10, como `1234567890`) lance un error de validación `ValidationError`.
3. **`test_01_technician_validation_invalid_phone`**: Verifica que ingresar un número de teléfono con una longitud diferente a 10 dígitos lance un error `ValidationError`.

### Pruebas de Sincronización del Estado de Equipos
4. **`test_02_equipment_status_sync`**: Comprueba que al mover las etapas de un ticket de mantenimiento (`nuevo` $\to$ `en_proceso` $\to$ `pendiente` $\to$ `finalizado`), el estado físico del equipo se actualice sincrónicamente (`received` $\to$ `under_repair` $\to$ `under_repair` $\to$ `repaired`).
5. **`test_03_technician_received_only_constraint`**: Evalúa que un usuario técnico no pueda abrir un ticket de mantenimiento sobre un equipo que ya está en reparación (el estado físico del equipo debe ser obligatoriamente `'received'`).
6. **`test_04_equipment_physical_state_default`**: Verifica que al registrar un nuevo equipo, su estado físico por defecto se inicialice en la categoría `'nuevo'`.

### Pruebas de Límites de Seguridad e Historial
7. **`test_05_technician_cannot_modify_history`**: Asegura que un técnico no pueda crear, modificar ni eliminar registros de forma directa en el modelo del historial `techstore.maintenance.history`, lanzando un error controlado de tipo `UserError`.
8. **`test_06_block_edit_when_finalizado_or_cancelado`**: Verifica que no sea posible modificar los campos del ticket una vez que este ha sido transicionado a los estados finales `finalizado` o `cancelado`.

### Pruebas de Wizards de Transición
9. **`test_07_state_wizard_comment_sync`**: Comprueba que al ejecutar la acción de confirmación del asistente transitorio (`techstore.maintenance.state.wizard`), el ticket cambie de estado y el comentario del usuario se guarde correctamente en el historial de auditoría.
10. **`test_08_cannot_start_without_technician`**: Asegura que al intentar pasar un ticket al estado `en_proceso` sin antes asignarle un técnico de soporte, el sistema bloquee la acción lanzando un error `ValidationError` (aplica para modificación directa y ejecución mediante wizard).

### Restricciones para la Finalización
11. **`test_09_validation_finalizado_missing_fields`**: Evalúa que el sistema bloquee la finalización de un mantenimiento si el técnico no ha ingresado el `diagnosis` o la `solution`.
12. **`test_10_validation_finalizado_zero_costs`**: Valida que se lance un error `ValidationError` si el técnico intenta marcar como completado un ticket con `estimated_cost = 0.0` o `final_cost = 0.0`.
13. **`test_11_validation_finalizado_success`**: Confirma que el ticket pase correctamente a `finalizado` cuando se proporcionan valores válidos para diagnóstico, solución y costos superiores a cero.

### Validaciones de Fechas y Autocompletado
14. **`test_12_equipment_problem_description_required`**: Valida que no se pueda registrar un equipo sin ingresar una descripción detallada del problema.
15. **`test_13_maintenance_auto_copy_problem_description`**: Comprueba que al abrir una orden de servicio de mantenimiento con descripción vacía, el sistema copie por defecto la descripción del problema asociada al equipo.
16. **`test_14_validation_finalizado_invalid_end_date_past`**: Verifica que pasar un ticket a `finalizado` con una fecha de fin (`end_date`) en el pasado (anterior al día de hoy) lance un error `ValidationError`.
17. **`test_15_validation_finalizado_invalid_end_date_before_start`**: Verifica que el sistema bloquee la finalización si la fecha de fin es anterior a la fecha de inicio.
18. **`test_16_block_edit_end_date_when_finalizado`**: Comprueba que un técnico no pueda alterar el campo `end_date` una vez finalizado el ticket.

### Pruebas de Control de Acceso por Roles
19. **`test_17_technician_readonly_field`**: Evalúa que el campo computado `is_technician_readonly` devuelva `True` para los usuarios técnicos y `False` para los administradores.
20. **`test_18_technician_state_change_restriction`**: Comprueba que los técnicos tengan prohibido modificar los estados de los mantenimientos asignados a otros técnicos.
21. **`test_19_technician_created_maintenance_flow`**: Verifica el flujo completo del ciclo de vida (`nuevo` $\to$ `en_proceso` $\to$ `pendiente` $\to$ `en_proceso` $\to$ `finalizado`) ejecutado por un técnico sobre un ticket creado por él mismo.

### Pruebas del Motor de Reportes
22. **`test_20_report_wizard_admin_flow`**: Comprueba que el rol administrador pueda configurar libremente el generador de reportes para descargar reportes detallados y consolidados de todo el sistema.
23. **`test_21_report_wizard_technician_flow`**: Comprueba que los técnicos estén limitados a exportar reportes detallados únicamente de sus mantenimientos asignados, bloqueando intentos de generar el consolidado general.
24. **`test_22_report_wizard_excel_generation`**: Comprueba que el wizard de reportes genere correctamente los archivos binarios Excel en formato XLSX aplicando los estilos de color correspondientes.

### Pruebas del Tablero Kanban
25. **`test_23_kanban_group_expansion`**: Valida que la estructura del tablero Kanban mantenga el orden de etapas requerido: `['nuevo', 'asignado', 'en_proceso', 'pendiente', 'finalizado', 'cancelado']`.

---

## 4. Cómo ejecutar las pruebas unitarias

Las pruebas deben ejecutarse activando el modo test de Odoo al inicializar el servidor.

### Ejecución usando Docker:
Desde la terminal en el directorio raíz de la aplicación, ejecute el siguiente comando para correr las pruebas unitarias del módulo y detener el contenedor al finalizar:

```bash
docker-compose exec odoo odoo -c /etc/odoo/odoo.conf -d odoo_db -i techstore_maintenance --test-enable --stop-after-init
```

*Nota: Cambie `odoo_db` por el nombre de la base de datos de su entorno de desarrollo si este difiere.*
*Explicación de parámetros:*
* `-c /etc/odoo/odoo.conf`: Ruta al archivo de configuración de Odoo en el contenedor.
* `-d odoo_db`: Base de datos de pruebas sobre la cual se ejecutará la suite.
* `-i techstore_maintenance`: Fuerza la reinstalación/actualización del módulo antes de correr los tests.
* `--test-enable`: Habilita el cargador de pruebas unitarias de Odoo.
* `--stop-after-init`: Detiene inmediatamente el servidor de Odoo cuando la ejecución de todas las pruebas haya finalizado (evitando que Odoo continúe ejecutándose en segundo plano).
