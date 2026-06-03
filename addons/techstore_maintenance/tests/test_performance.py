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
    Suite de Pruebas de Rendimiento para TechStore Maintenance.
    Evalúa la capacidad de respuesta en operaciones frecuentes:
    carga de vistas, cambios de estado, cálculos automáticos y filtros.
    """

    @classmethod
    def setUpClass(cls):
        super(TestTechStorePerformance, cls).setUpClass()

        cls.partner = cls.env['res.partner'].create({
            'name': 'Cliente Performance SRL',
            'email': 'perf@techstore.com',
            'phone': '123-456'
        })

        cls.technician = cls.env['techstore.technician'].create({
            'name': 'Técnico Performance',
            'identification': 'ID-PERF-001',
            'phone': '999-999',
            'email': 'tecnico.perf@techstore.com'
        })

        cls.technician2 = cls.env['techstore.technician'].create({
            'name': 'Técnico Performance 2',
            'identification': 'ID-PERF-002',
            'phone': '888-888',
            'email': 'tecnico2.perf@techstore.com'
        })

        cls.equipment = cls.env['techstore.equipment'].create({
            'partner_id': cls.partner.id,
            'equipment_type': 'server',
            'brand': 'ServerLoad',
            'serial_number': 'SN-PERF-001',
        })

        cls.equipment2 = cls.env['techstore.equipment'].create({
            'partner_id': cls.partner.id,
            'equipment_type': 'laptop',
            'brand': 'LoadBook',
            'serial_number': 'SN-PERF-002',
        })

        # Población de 200 mantenimientos para simular carga real
        cls.maintenances = []
        types = ['preventive', 'corrective', 'diagnostic']
        states = ['nuevo', 'asignado', 'en_proceso', 'pendiente', 'finalizado', 'cancelado']
        priorities = ['0', '1', '2', '3']

        for i in range(200):
            equip = cls.equipment if i % 2 == 0 else cls.equipment2
            tech = cls.technician if i % 3 != 0 else cls.technician2
            maint = cls.env['techstore.maintenance'].create({
                'partner_id': cls.partner.id,
                'equipment_id': equip.id,
                'technician_id': tech.id,
                'description': f'Orden rendimiento QA-{i}',
                'maintenance_type': types[i % 3],
                'priority': priorities[i % 4],
                'state': states[i % 6],
                'estimated_time': 4.0,
                'diagnosis': f'Diagnóstico generado para orden {i}',
            })
            cls.maintenances.append(maint)

    @staticmethod
    def _calculate_statistics(times):
        t_min = min(times)
        t_max = max(times)
        t_avg = sum(times) / len(times)
        variance = sum((x - t_avg) ** 2 for x in times) / len(times)
        t_stddev = math.sqrt(variance)
        return t_min, t_max, t_avg, t_stddev

    def test_pr01_tree_view_load(self):
        """PR-01: Carga de vista tree - simular apertura de lista de mantenimientos."""
        _logger.info("=== PR-01: CARGA DE VISTA TREE (200 registros) ===")

        times = []
        for _ in range(5):
            t_start = time.perf_counter()
            records = self.env['techstore.maintenance'].search_read(
                domain=[],
                fields=['number', 'state', 'priority', 'maintenance_type',
                        'technician_id', 'create_date'],
                limit=None
            )
            t_end = time.perf_counter()
            times.append(t_end - t_start)

        _min, _max, _avg, _std = self._calculate_statistics(times)
        _logger.info(
            f"  TREE VIEW | N=5 | MIN={_min:.4f}s | MAX={_max:.4f}s | "
            f"AVG={_avg:.4f}s | STD={_std:.4f}s | registros={len(records)}"
        )
        self.assertLess(_avg, 1.0,
                        f"PR-01: Tiempo promedio de carga ({_avg:.4f}s) supera 1.0s.")

    def test_pr02_kanban_view_load(self):
        """PR-02: Carga de vista kanban - agrupar mantenimientos por estado."""
        _logger.info("=== PR-02: CARGA DE VISTA KANBAN (agrupación por estado) ===")

        times = []
        for _ in range(5):
            t_start = time.perf_counter()
            grouped = self.env['techstore.maintenance'].read_group(
                domain=[],
                fields=['state', 'id:count'],
                groupby=['state'],
                lazy=False
            )
            t_end = time.perf_counter()
            times.append(t_end - t_start)

        _min, _max, _avg, _std = self._calculate_statistics(times)
        _logger.info(
            f"  KANBAN    | N=5 | MIN={_min:.4f}s | MAX={_max:.4f}s | "
            f"AVG={_avg:.4f}s | STD={_std:.4f}s | grupos={len(grouped)}"
        )
        self.assertLess(_avg, 1.0,
                        f"PR-02: Tiempo promedio de carga kanban ({_avg:.4f}s) supera 1.0s.")

    def test_pr03_auto_calculation(self):
        """PR-03: Cálculo automático - medir tiempo al guardar mantenimiento con métricas."""
        _logger.info("=== PR-03: CÁLCULO AUTOMÁTICO DE MÉTRICAS ===")

        times = []
        for i in range(20):
            t_start = time.perf_counter()
            maint = self.env['techstore.maintenance'].create({
                'partner_id': self.partner.id,
                'equipment_id': self.equipment.id,
                'description': f'Métrica automática {i}',
                'maintenance_type': 'preventive',
                'estimated_time': 2.0,
            })
            maint.write({
                'state': 'finalizado',
                'customer_satisfaction': '4',
            })
            # Forzar recálculo de métricas
            metrics = self.env['techstore.maintenance.metrics'].search([
                ('maintenance_id', '=', maint.id)
            ])
            metrics._compute_metrics()
            t_end = time.perf_counter()
            times.append(t_end - t_start)

        _min, _max, _avg, _std = self._calculate_statistics(times)
        _logger.info(
            f"  MÉTRICAS  | N=20 | MIN={_min:.4f}s | MAX={_max:.4f}s | "
            f"AVG={_avg:.4f}s | STD={_std:.4f}s"
        )
        self.assertLess(_avg, 1.0,
                        f"PR-03: Tiempo promedio de cálculo ({_avg:.4f}s) supera 1.0s.")

    def test_pr04_state_change(self):
        """PR-04: Cambio de estado - medir tiempo al pasar de nuevo a en_proceso."""
        _logger.info("=== PR-04: CAMBIO DE ESTADO (nuevo -> en_proceso) ===")

        # Crear 20 mantenimientos nuevos para la prueba
        test_maints = []
        for i in range(20):
            m = self.env['techstore.maintenance'].create({
                'partner_id': self.partner.id,
                'equipment_id': self.equipment.id,
                'technician_id': self.technician.id,
                'description': f'Cambio estado {i}',
                'maintenance_type': 'corrective',
            })
            test_maints.append(m)

        times = []
        for m in test_maints:
            t_start = time.perf_counter()
            m.write({'state': 'en_proceso'})
            t_end = time.perf_counter()
            times.append(t_end - t_start)

        _min, _max, _avg, _std = self._calculate_statistics(times)
        _logger.info(
            f"  STATE CHG | N=20 | MIN={_min:.4f}s | MAX={_max:.4f}s | "
            f"AVG={_avg:.4f}s | STD={_std:.4f}s"
        )
        self.assertLess(_avg, 1.0,
                        f"PR-04: Tiempo promedio de cambio de estado ({_avg:.4f}s) supera 1.0s.")

    def test_pr05_metrics_consultation(self):
        """PR-05: Consulta de métricas - pivot y gráfica sobre datos agrupados."""
        _logger.info("=== PR-05: CONSULTA DE MÉTRICAS (pivot y gráfica) ===")

        # Asegurar que existan métricas calculadas
        for m in self.maintenances[:10]:
            if m.state == 'finalizado':
                metrics = self.env['techstore.maintenance.metrics'].search([
                    ('maintenance_id', '=', m.id)
                ])
                if metrics:
                    metrics._compute_metrics()

        times_pivot = []
        for _ in range(5):
            t_start = time.perf_counter()
            pivot_data = self.env['techstore.maintenance.metrics'].read_group(
                domain=[],
                fields=['maintenance_type', 'attention_time:avg',
                        'resolution_time:avg', 'delay:avg', 'technician_efficiency:avg',
                        'quality_indicator:avg', 'id:count'],
                groupby=['maintenance_type'],
                lazy=False
            )
            t_end = time.perf_counter()
            times_pivot.append(t_end - t_start)

        _min, _max, _avg, _std = self._calculate_statistics(times_pivot)
        _logger.info(
            f"  PIVOT     | N=5 | MIN={_min:.4f}s | MAX={_max:.4f}s | "
            f"AVG={_avg:.4f}s | STD={_std:.4f}s | grupos={len(pivot_data)}"
        )
        self.assertLess(_avg, 1.0,
                        f"PR-05: Tiempo promedio de consulta pivot ({_avg:.4f}s) supera 1.0s.")

        # Gráfica: agrupar por técnico
        times_graph = []
        for _ in range(5):
            t_start = time.perf_counter()
            graph_data = self.env['techstore.maintenance.metrics'].read_group(
                domain=[],
                fields=['technician_id', 'resolution_time:avg', 'id:count'],
                groupby=['technician_id'],
                lazy=False
            )
            t_end = time.perf_counter()
            times_graph.append(t_end - t_start)

        _min2, _max2, _avg2, _std2 = self._calculate_statistics(times_graph)
        _logger.info(
            f"  GRAPH     | N=5 | MIN={_min2:.4f}s | MAX={_max2:.4f}s | "
            f"AVG={_avg2:.4f}s | STD={_std2:.4f}s | grupos={len(graph_data)}"
        )
        self.assertLess(_avg2, 1.0,
                        f"PR-05: Tiempo promedio de consulta gráfica ({_avg2:.4f}s) supera 1.0s.")

    def test_pr06_search_and_filter(self):
        """PR-06: Búsqueda y filtrado - aplicar filtros por técnico, estado y prioridad."""
        _logger.info("=== PR-06: BÚSQUEDA Y FILTRADO ===")

        # Filtro por técnico
        times_tech = []
        for _ in range(10):
            t_start = time.perf_counter()
            records = self.env['techstore.maintenance'].search_read(
                domain=[('technician_id', '=', self.technician.id)],
                fields=['number', 'state', 'priority'],
                limit=None
            )
            t_end = time.perf_counter()
            times_tech.append(t_end - t_start)

        _min, _max, _avg_tech, _std = self._calculate_statistics(times_tech)
        _logger.info(
            f"  FILTRO TÉC. | N=10 | MIN={_min:.4f}s | MAX={_max:.4f}s | "
            f"AVG={_avg_tech:.4f}s | STD={_std:.4f}s | resultados={len(records)}"
        )

        # Filtro por estado
        times_state = []
        for _ in range(10):
            t_start = time.perf_counter()
            records = self.env['techstore.maintenance'].search_read(
                domain=[('state', '=', 'en_proceso')],
                fields=['number', 'technician_id', 'priority'],
                limit=None
            )
            t_end = time.perf_counter()
            times_state.append(t_end - t_start)

        _min2, _max2, _avg_state, _std2 = self._calculate_statistics(times_state)
        _logger.info(
            f"  FILTRO EST. | N=10 | MIN={_min2:.4f}s | MAX={_max2:.4f}s | "
            f"AVG={_avg_state:.4f}s | STD={_std2:.4f}s | resultados={len(records)}"
        )

        # Filtro por prioridad
        times_prio = []
        for _ in range(10):
            t_start = time.perf_counter()
            records = self.env['techstore.maintenance'].search_read(
                domain=[('priority', '=', '3')],
                fields=['number', 'state', 'technician_id'],
                limit=None
            )
            t_end = time.perf_counter()
            times_prio.append(t_end - t_start)

        _min3, _max3, _avg_prio, _std3 = self._calculate_statistics(times_prio)
        _logger.info(
            f"  FILTRO PRI. | N=10 | MIN={_min3:.4f}s | MAX={_max3:.4f}s | "
            f"AVG={_avg_prio:.4f}s | STD={_std3:.4f}s | resultados={len(records)}"
        )

        # Filtro combinado (técnico + estado + prioridad)
        times_comb = []
        for _ in range(10):
            t_start = time.perf_counter()
            records = self.env['techstore.maintenance'].search_read(
                domain=[
                    ('technician_id', '=', self.technician.id),
                    ('state', '=', 'asignado'),
                    ('priority', '=', '1'),
                ],
                fields=['number', 'state'],
                limit=None
            )
            t_end = time.perf_counter()
            times_comb.append(t_end - t_start)

        _min4, _max4, _avg_comb, _std4 = self._calculate_statistics(times_comb)
        _logger.info(
            f"  FILTRO COMB. | N=10 | MIN={_min4:.4f}s | MAX={_max4:.4f}s | "
            f"AVG={_avg_comb:.4f}s | STD={_std4:.4f}s | resultados={len(records)}"
        )

        overall_avg = (_avg_tech + _avg_state + _avg_prio + _avg_comb) / 4
        _logger.info(
            f"  >>> PROMEDIO GENERAL FILTROS: {overall_avg:.4f}s"
        )
        self.assertLess(overall_avg, 1.0,
                        f"PR-06: Tiempo promedio de filtros ({overall_avg:.4f}s) supera 1.0s.")
