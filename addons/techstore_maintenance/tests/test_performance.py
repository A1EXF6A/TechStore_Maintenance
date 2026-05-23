# -*- coding: utf-8 -*-
# pyrefly: ignore [missing-import]
import time
import math
import logging
# pyrefly: ignore [missing-import]
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)

class TestTechStorePerformance(TransactionCase):
    """
    Suite de Pruebas de Rendimiento y Carga para TechStore Maintenance.
    Realiza operaciones masivas, registra los tiempos individuales empleando timers de alta resolución,
    y calcula indicadores estadísticos descriptivos (Media, Mínimo, Máximo, Desviación Estándar).
    """

    @classmethod
    def setUpClass(cls):
        super(TestTechStorePerformance, cls).setUpClass()
        
        # Crear registros base para las operaciones CRUD
        cls.partner = cls.env['res.partner'].create({
            'name': 'Cliente Performance SRL',
            'email': 'perf@techstore.com',
            'phone': '123-456'
        })
        
        cls.technician = cls.env['techstore.technician'].create({
            'name': 'Técnico Senior de Estrés',
            'identification': 'ID-PERF-99',
            'phone': '999-999',
            'email': 'tecnico.perf@techstore.com'
        })
        
        cls.equipment = cls.env['techstore.equipment'].create({
            'partner_id': cls.partner.id,
            'equipment_type': 'server',
            'brand': 'ServerLoad',
            'serial_number': 'SN-PERF-999',
        })

    def test_01_crud_mass_simulation(self):
        """Simular 200 operaciones CRUD y evaluar latencias promedio, máximas, mínimas y desviación estándar."""
        num_records = 200
        _logger.info("=== INICIANDO PRUEBAS DE ESTRÉS DE RENDIMIENTO: 200 OPERACIONES CRUD ===")

        # ---------------------------------------------------------
        # 1. SIMULACIÓN DE CREACIÓN (CREATE)
        # ---------------------------------------------------------
        create_times = []
        maintenances = []
        
        for i in range(num_records):
            t_start = time.perf_counter()
            m = self.env['techstore.maintenance'].create({
                'partner_id': self.partner.id,
                'equipment_id': self.equipment.id,
                'technician_id': self.technician.id,
                'description': f'Orden de estrés QA-PERF-{i}',
                'maintenance_type': 'corrective',
                'estimated_time': 4.0
            })
            t_end = time.perf_counter()
            create_times.append(t_end - t_start)
            maintenances.append(m)

        # ---------------------------------------------------------
        # 2. SIMULACIÓN DE LECTURA (READ)
        # ---------------------------------------------------------
        read_times = []
        for m in maintenances:
            t_start = time.perf_counter()
            # Leer varios campos representativos del modelo, incluyendo campos calculados
            _ = m.read(['number', 'state', 'description', 'real_time', 'create_date'])
            t_end = time.perf_counter()
            read_times.append(t_end - t_start)

        # ---------------------------------------------------------
        # 3. SIMULACIÓN DE ACTUALIZACIÓN (WRITE)
        # ---------------------------------------------------------
        # Modificar el estado a 'en_proceso' para disparar el flujo de logs de historial
        write_times = []
        for m in maintenances:
            t_start = time.perf_counter()
            m.write({'state': 'en_proceso'})
            t_end = time.perf_counter()
            write_times.append(t_end - t_start)

        # ---------------------------------------------------------
        # 4. ANÁLISIS ESTADÍSTICO
        # ---------------------------------------------------------
        def calculate_statistics(times):
            t_min = min(times)
            t_max = max(times)
            t_avg = sum(times) / len(times)
            
            # Desviación Estándar poblacional
            variance = sum((x - t_avg) ** 2 for x in times) / len(times)
            t_stddev = math.sqrt(variance)
            
            return t_min, t_max, t_avg, t_stddev

        c_min, c_max, c_avg, c_stddev = calculate_statistics(create_times)
        r_min, r_max, r_avg, r_stddev = calculate_statistics(read_times)
        w_min, w_max, w_avg, w_stddev = calculate_statistics(write_times)

        # Construcción de la tabla de salida formateada en logs
        report_table = (
            "\n" + "="*95 + "\n" +
            "                    RESUMEN DE TIEMPOS DE RESPUESTA - OPERACIONES CRUD (SEGUNDOS)\n" +
            "-"*95 + "\n" +
            "  OPERACIÓN |   N   |   MÍNIMO (s)   |   MÁXIMO (s)   |   PROMEDIO (s)   |  DESV. ESTÁNDAR (s)\n" +
            "-"*95 + "\n" +
            f"  CREATE    |  {num_records:3d}  |    {c_min:.6f}    |    {c_max:.6f}    |     {c_avg:.6f}     |      {c_stddev:.6f}\n" +
            f"  READ      |  {num_records:3d}  |    {r_min:.6f}    |    {r_max:.6f}    |     {r_avg:.6f}     |      {r_stddev:.6f}\n" +
            f"  WRITE     |  {num_records:3d}  |    {w_min:.6f}    |    {w_max:.6f}    |     {w_avg:.6f}     |      {w_stddev:.6f}\n" +
            "="*95
        )
        
        _logger.info(report_table)

        # ---------------------------------------------------------
        # 5. ASERCIONES Y NORMAS DE CALIDAD
        # ---------------------------------------------------------
        # Según el taller final y estándares, un tiempo promedio superior a 1s se cataloga como lento.
        # Impondremos aserciones de límite de 1 segundo para asegurar la fluidez.
        self.assertLess(c_avg, 1.0, f"El tiempo promedio de creación ({c_avg:.4f}s) supera el límite aceptable de 1.0s.")
        self.assertLess(r_avg, 0.5, f"El tiempo promedio de lectura ({r_avg:.4f}s) supera el límite aceptable de 0.5s.")
        self.assertLess(w_avg, 1.0, f"El tiempo promedio de actualización ({w_avg:.4f}s) supera el límite aceptable de 1.0s.")
