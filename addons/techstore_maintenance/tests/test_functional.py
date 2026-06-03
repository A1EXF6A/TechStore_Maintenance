# -*- coding: utf-8 -*-
# pyrefly: ignore [missing-import]
from odoo.tests.common import TransactionCase
# pyrefly: ignore [missing-import]
from odoo.exceptions import ValidationError
# pyrefly: ignore [missing-import]
from odoo.tools import mute_logger
import psycopg2

class TestTechStoreFunctional(TransactionCase):
    """
    Suite de Pruebas Funcionales para el módulo TechStore Maintenance.
    Valida la integridad de datos, restricciones de negocio, flujos de estados
    y las automatizaciones asociadas.
    """

    @classmethod
    def setUpClass(cls):
        super(TestTechStoreFunctional, cls).setUpClass()
        
        # Crear datos de prueba base comunes
        cls.partner = cls.env['res.partner'].create({
            'name': 'Cliente de Prueba QA',
            'email': 'cliente.qa@example.com',
            'phone': '+1 555-0199'
        })
        
        cls.technician = cls.env['techstore.technician'].create({
            'name': 'Técnico Especialista QA',
            'identification': 'ID-100200',
            'phone': '555-1234',
            'email': 'tecnico.qa@techstore.com',
            'specialty': 'hardware'
        })
        
        cls.equipment = cls.env['techstore.equipment'].create({
            'partner_id': cls.partner.id,
            'equipment_type': 'laptop',
            'brand': 'TechBrand',
            'model': 'SuperPro 2026',
            'serial_number': 'SN-QA-999',
            'has_warranty': True,
            'problem_description': 'Falla intermitente en teclado.'
        })

    def test_01_technician_fields_and_validation(self):
        """TC-01: Validar creación de Técnico con datos correctos y disparar validaciones de email."""
        # Caso exitoso
        tech = self.env['techstore.technician'].create({
            'name': 'Tecnico Exitoso',
            'identification': 'ID-UNIQUE-001',
            'phone': '333-3333',
            'email': 'valido@techstore.com'
        })
        self.assertTrue(tech.id, "El técnico con datos correctos debería ser creado.")

        # TC-02: Validar ValidationError por correo inválido
        with self.assertRaises(ValidationError, msg="Se esperaba ValidationError por formato de email inválido."):
            self.env['techstore.technician'].create({
                'name': 'Tecnico Error Email',
                'identification': 'ID-ERROR-001',
                'phone': '444-4444',
                'email': 'correo_sin_arroba.com'
            })

    def test_02_technician_unique_identification(self):
        """TC-03: Validar la restricción SQL unique de identificación del técnico."""
        # Se intenta duplicar la identificación de cls.technician ('ID-100200')
        # Usamos savepoint para evitar abortar la transacción de la suite de pruebas
        with self.assertRaises(psycopg2.IntegrityError, msg="Se esperaba un error de integridad de base de datos por identificación duplicada."):
            with self.cr.savepoint():
                self.env['techstore.technician'].create({
                    'name': 'Tecnico Duplicado',
                    'identification': 'ID-100200', # Duplicada
                    'phone': '999-9999'
                })

    def test_03_equipment_unique_serial_number(self):
        """TC-04: Validar la restricción SQL unique de número de serie en equipos."""
        # Se intenta duplicar el serial de cls.equipment ('SN-QA-999')
        with self.assertRaises(psycopg2.IntegrityError, msg="Se esperaba un error de integridad por número de serie duplicado."):
            with self.cr.savepoint():
                self.env['techstore.equipment'].create({
                    'partner_id': self.partner.id,
                    'equipment_type': 'desktop',
                    'serial_number': 'SN-QA-999', # Duplicada
                })

    def test_04_maintenance_creation_and_sequences(self):
        """TC-05: Validar generación de secuencias automáticas, estado inicial y creación de logs/métricas."""
        maint = self.env['techstore.maintenance'].create({
            'partner_id': self.partner.id,
            'equipment_id': self.equipment.id,
            'description': 'Mantenimiento preventivo rutinario',
            'maintenance_type': 'preventive'
        })
        
        # Validar secuencia de número no es nula ni 'New'
        self.assertIsNotNone(maint.number, "El número de mantenimiento no debe ser nulo.")
        self.assertNotEqual(maint.number, 'New', "El número debe haberse generado a partir de la secuencia.")
        
        # Validar estado inicial 'nuevo'
        self.assertEqual(maint.state, 'nuevo', "El estado por defecto debe ser 'nuevo'.")
        
        # TC-05 (Auditoría): Validar creación automática de historial de cambios
        history = self.env['techstore.maintenance.history'].search([('maintenance_id', '=', maint.id)])
        self.assertEqual(len(history), 1, "Debería haberse creado 1 registro en el historial.")
        self.assertEqual(history.new_state, 'nuevo', "El estado registrado en el historial debe ser 'nuevo'.")
        
        # Validar creación automática del registro de métricas vacías
        metrics = self.env['techstore.maintenance.metrics'].search([('maintenance_id', '=', maint.id)])
        self.assertEqual(len(metrics), 1, "Debería haberse creado 1 registro en la tabla de métricas.")

    def test_05_maintenance_state_flow_and_dates(self):
        """TC-06 y TC-07: Validar flujo de estados, auto-estampado de fechas, tiempo real y métricas finales."""
        maint = self.env['techstore.maintenance'].create({
            'partner_id': self.partner.id,
            'equipment_id': self.equipment.id,
            'description': 'Mantenimiento correctivo de hardware',
            'maintenance_type': 'corrective',
            'estimated_time': 2.0
        })

        # Precondiciones
        self.assertFalse(maint.start_date, "La fecha de inicio debe estar vacía inicialmente.")
        self.assertFalse(maint.end_date, "La fecha de fin debe estar vacía inicialmente.")

        # Transición: nuevo -> asignado
        maint.write({
            'state': 'asignado',
            'technician_id': self.technician.id
        })
        self.assertEqual(maint.state, 'asignado', "El estado debe ser 'asignado'.")
        
        # Transición: asignado -> en_proceso (Dispara fecha de inicio)
        maint.write({'state': 'en_proceso'})
        self.assertEqual(maint.state, 'en_proceso', "El estado debe ser 'en_proceso'.")
        self.assertTrue(maint.start_date, "La fecha de inicio debe haberse registrado automáticamente.")

        # Transición: en_proceso -> finalizado (Dispara fecha de fin, tiempo real y métricas)
        maint.write({
            'state': 'finalizado',
            'customer_satisfaction': '4',
            'solution': 'Se cambió la memoria RAM defectuosa.'
        })
        self.assertEqual(maint.state, 'finalizado', "El estado debe ser 'finalizado'.")
        self.assertTrue(maint.end_date, "La fecha de fin debe haberse registrado automáticamente.")
        
        # Verificar que real_time se haya calculado
        self.assertGreaterEqual(maint.real_time, 0.0, "El tiempo real empleado debe ser mayor o igual a 0.")

        # Validar cálculo de métricas de calidad y SLA
        metrics = self.env['techstore.maintenance.metrics'].search([('maintenance_id', '=', maint.id)])
        self.assertTrue(metrics.sla_compliance, "El mantenimiento debe cumplir SLA porque el tiempo real es cercano a 0.")
        self.assertEqual(metrics.quality_indicator, 100.0, "El indicador de calidad debe ser 100% para una satisfacción Excelente (4).")

    def test_06_technician_workload_level(self):
        """TC-08: Validar cálculo dinámico del nivel de carga de trabajo de los técnicos."""
        # Validar estado inicial (carga 'low')
        self.assertEqual(self.technician.maintenance_count, 0, "Inicialmente el técnico no debe tener órdenes asignadas.")
        self.assertEqual(self.technician.workload_level, 'low', "El nivel de carga debe ser 'low'.")

        # Asignar 3 mantenimientos en estado 'asignado'
        maint_list = []
        for i in range(3):
            m = self.env['techstore.maintenance'].create({
                'partner_id': self.partner.id,
                'equipment_id': self.equipment.id,
                'technician_id': self.technician.id,
                'description': f'Orden QA de prueba {i}',
                'state': 'asignado'
            })
            maint_list.append(m)

        # Provocar recomputación en la instancia del técnico
        self.technician._compute_maintenance_count()
        self.technician._compute_workload_level()

        # Debe ser 'medium' (entre 3 y 5)
        self.assertEqual(self.technician.maintenance_count, 3, "El conteo de mantenimientos debe ser 3.")
        self.assertEqual(self.technician.workload_level, 'medium', "El nivel de carga debe ser 'medium' con 3 órdenes activas.")

        # Añadir 3 más (Total 6, nivel de carga 'high' entre 6 y 8)
        for i in range(3, 6):
            self.env['techstore.maintenance'].create({
                'partner_id': self.partner.id,
                'equipment_id': self.equipment.id,
                'technician_id': self.technician.id,
                'description': f'Orden QA de prueba {i}',
                'state': 'asignado'
            })

        self.technician._compute_maintenance_count()
        self.technician._compute_workload_level()
        self.assertEqual(self.technician.maintenance_count, 6, "El conteo debe ser 6.")
        self.assertEqual(self.technician.workload_level, 'high', "El nivel de carga debe ser 'high' con 6 órdenes activas.")

        # Finalizar un mantenimiento, debe bajar a 5 y por lo tanto a 'medium'
        maint_list[0].write({'state': 'finalizado'})
        
        self.technician._compute_maintenance_count()
        self.technician._compute_workload_level()
        self.assertEqual(self.technician.maintenance_count, 5, "El conteo debe ser 5 tras finalizar una orden.")
        self.assertEqual(self.technician.workload_level, 'medium', "El nivel de carga debe regresar a 'medium'.")

    def test_07_equipment_auto_code_and_state(self):
        """CF-06/CF-08: Validar código secuencial al crear equipo y cambios de estado."""
        equip = self.env['techstore.equipment'].create({
            'partner_id': self.partner.id,
            'equipment_type': 'desktop',
            'brand': 'HP',
            'serial_number': 'SN-CF-UNIQUE-001',
        })
        self.assertTrue(equip.code, "El código del equipo no debe ser vacío.")
        self.assertNotEqual(equip.code, 'New', "El código debe generarse desde la secuencia.")
        self.assertIn('EQUIP', equip.code, "El código debe contener el prefijo EQUIP.")

        self.assertEqual(equip.state, 'received', "El estado inicial debe ser 'received'.")
        equip.write({'state': 'under_repair'})
        self.assertEqual(equip.state, 'under_repair', "El estado debe actualizarse a 'under_repair'.")
        equip.write({'state': 'repaired'})
        self.assertEqual(equip.state, 'repaired', "El estado debe actualizarse a 'repaired'.")
        equip.write({'state': 'delivered'})
        self.assertEqual(equip.state, 'delivered', "El estado debe actualizarse a 'delivered'.")

    def test_08_chatter_trackable_fields(self):
        """CF-05: Verificar que los campos trazables (tracking=True) se registren en el chatter."""
        tech = self.env['techstore.technician'].create({
            'name': 'Técnico Chatter',
            'identification': 'ID-CHATTER-001',
            'phone': '111-222',
            'email': 'chatter@techstore.com'
        })
        # Verificar que los campos del modelo tienen tracking habilitado en su definición
        track_fields = tech._track_get_fields()
        self.assertIn('name', track_fields, "El campo 'name' debe tener tracking habilitado.")
        self.assertIn('identification', track_fields, "El campo 'identification' debe tener tracking habilitado.")
        self.assertIn('phone', track_fields, "El campo 'phone' debe tener tracking habilitado.")
        self.assertIn('email', track_fields, "El campo 'email' debe tener tracking habilitado.")
        self.assertIn('specialty', track_fields, "El campo 'specialty' debe tener tracking habilitado.")
        self.assertIn('user_id', track_fields, "El campo 'user_id' debe tener tracking habilitado.")

        # Verificar que la escritura del campo persiste correctamente
        tech.write({'name': 'Técnico Chatter Actualizado'})
        self.assertEqual(tech.name, 'Técnico Chatter Actualizado', "El nombre debe haberse actualizado correctamente.")

    def test_09_critical_priority_warning(self):
        """CF-12: Validar que al seleccionar prioridad crítica se emita una advertencia."""
        maint = self.env['techstore.maintenance'].new({
            'partner_id': self.partner.id,
            'equipment_id': self.equipment.id,
            'description': 'Mantenimiento con prioridad crítica',
            'maintenance_type': 'corrective',
        })
        maint.priority = '3'
        result = maint._onchange_priority()
        self.assertIsNotNone(result, "El onchange debe devolver un diccionario con advertencia.")
        self.assertIn('warning', result, "El resultado debe contener una clave 'warning'.")
        self.assertIn('Critical', result['warning']['title'], "El título de la advertencia debe mencionar 'Critical'.")

    def test_10_history_ordering(self):
        """CF-14: Validar que el historial de cambios se ordene por fecha descendente."""
        maint = self.env['techstore.maintenance'].create({
            'partner_id': self.partner.id,
            'equipment_id': self.equipment.id,
            'description': 'Test historial descendente',
            'maintenance_type': 'diagnostic',
        })
        maint.write({'state': 'asignado'})
        maint.write({'state': 'en_proceso'})
        maint.write({'state': 'finalizado'})

        history = self.env['techstore.maintenance.history'].search([
            ('maintenance_id', '=', maint.id)
        ])
        self.assertGreaterEqual(len(history), 4, "Debe haber al menos 4 registros de historial.")

        dates = [r.change_date for r in history]
        for i in range(len(dates) - 1):
            self.assertGreaterEqual(
                dates[i], dates[i + 1],
                "El historial debe estar ordenado por change_date descendente."
            )
