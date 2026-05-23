# -*- coding: utf-8 -*-
# pyrefly: ignore [missing-import]
from odoo.tests.common import TransactionCase
# pyrefly: ignore [missing-import]
from odoo.exceptions import AccessError

class TestTechStoreSecurity(TransactionCase):
    """
    Suite de Pruebas de Seguridad para el módulo TechStore Maintenance.
    Valida la segregación de funciones (SoD), las reglas de registro (Record Rules)
    y el cumplimiento de la matriz de permisos de accesos (ACLs).
    """

    @classmethod
    def setUpClass(cls):
        super(TestTechStoreSecurity, cls).setUpClass()

        # 1. Obtener las referencias de grupos de seguridad definidos
        cls.group_tech = cls.env.ref('techstore_maintenance.group_techstore_technician')
        cls.group_super = cls.env.ref('techstore_maintenance.group_techstore_supervisor')
        cls.group_admin = cls.env.ref('techstore_maintenance.group_techstore_admin')

        # 2. Crear usuarios y asociar sus respectivos grupos de seguridad
        # Técnico 1
        cls.user_tech_1 = cls.env['res.users'].create({
            'name': 'Técnico QA 1',
            'login': 'tech1_qa',
            'email': 'tech1@techstore.com',
            'groups_id': [(6, 0, [cls.group_tech.id])]
        })
        
        # Técnico 2
        cls.user_tech_2 = cls.env['res.users'].create({
            'name': 'Técnico QA 2',
            'login': 'tech2_qa',
            'email': 'tech2@techstore.com',
            'groups_id': [(6, 0, [cls.group_tech.id])]
        })

        # Supervisor
        cls.user_super = cls.env['res.users'].create({
            'name': 'Supervisor QA',
            'login': 'super_qa',
            'email': 'super@techstore.com',
            'groups_id': [(6, 0, [cls.group_super.id])]
        })

        # 3. Crear registros del modelo Técnico asociados a los usuarios correspondientes
        cls.partner = cls.env['res.partner'].create({'name': 'Cliente Corporativo SEC'})
        
        cls.equipment = cls.env['techstore.equipment'].create({
            'partner_id': cls.partner.id,
            'equipment_type': 'server',
            'brand': 'QA-Server',
            'serial_number': 'SN-SEC-999',
        })

        cls.tech_rec_1 = cls.env['techstore.technician'].create({
            'name': 'Técnico Físico 1',
            'identification': 'ID-TECH-SEC1',
            'phone': '111-222',
            'user_id': cls.user_tech_1.id
        })

        cls.tech_rec_2 = cls.env['techstore.technician'].create({
            'name': 'Técnico Físico 2',
            'identification': 'ID-TECH-SEC2',
            'phone': '333-444',
            'user_id': cls.user_tech_2.id
        })

        # 4. Crear mantenimientos asignados a cada técnico
        cls.maint_tech_1 = cls.env['techstore.maintenance'].create({
            'partner_id': cls.partner.id,
            'equipment_id': cls.equipment.id,
            'technician_id': cls.tech_rec_1.id,
            'description': 'Mantenimiento Servidor asignado a Técnico 1',
            'state': 'asignado'
        })

        cls.maint_tech_2 = cls.env['techstore.maintenance'].create({
            'partner_id': cls.partner.id,
            'equipment_id': cls.equipment.id,
            'technician_id': cls.tech_rec_2.id,
            'description': 'Mantenimiento Servidor asignado a Técnico 2',
            'state': 'asignado'
        })

    def test_01_record_rules_technician_isolation(self):
        """Validar que un técnico solo pueda ver y modificar sus mantenimientos asignados."""
        # 1. Búsqueda con usuario Técnico 1
        maint_tech1_env = self.env['techstore.maintenance'].with_user(self.user_tech_1)
        visible_maints = maint_tech1_env.search([])
        
        self.assertIn(self.maint_tech_1.id, visible_maints.ids, "Técnico 1 debería poder visualizar su propia orden asignada.")
        self.assertNotIn(self.maint_tech_2.id, visible_maints.ids, "Técnico 1 NO debería poder visualizar la orden del Técnico 2.")

        # 2. Intento de escritura en su propio registro (Debe permitir)
        try:
            self.maint_tech_1.with_user(self.user_tech_1).write({'observations': 'Nota de Técnico 1'})
        except AccessError:
            self.fail("El Técnico 1 debería poder escribir observaciones en su propia orden.")

        # 3. Intento de escritura en registro ajeno (Debe lanzar AccessError)
        with self.assertRaises(AccessError, msg="Se esperaba AccessError al intentar modificar un mantenimiento ajeno."):
            self.maint_tech_2.with_user(self.user_tech_1).write({'observations': 'Intruso Técnico 1'})

    def test_02_record_rules_supervisor_all_access(self):
        """Validar que un Supervisor pueda ver y modificar todas las órdenes."""
        maint_super_env = self.env['techstore.maintenance'].with_user(self.user_super)
        all_visible = maint_super_env.search([])
        
        self.assertIn(self.maint_tech_1.id, all_visible.ids, "El Supervisor debería ver la orden del Técnico 1.")
        self.assertIn(self.maint_tech_2.id, all_visible.ids, "El Supervisor debería ver la orden del Técnico 2.")

        # Modificación permitida de cualquier orden
        try:
            self.maint_tech_1.with_user(self.user_super).write({'observations': 'Supervisor revisando Técnico 1'})
            self.maint_tech_2.with_user(self.user_super).write({'observations': 'Supervisor revisando Técnico 2'})
        except AccessError:
            self.fail("El Supervisor debería tener permisos de escritura sobre cualquier orden de mantenimiento.")

    def test_03_acl_unlink_restrictions(self):
        """Validar que Técnicos y Supervisores no puedan eliminar (unlink) registros de mantenimiento."""
        # Intento por Técnico 1
        with self.assertRaises(AccessError, msg="Se esperaba AccessError: un técnico no puede eliminar órdenes de mantenimiento."):
            self.maint_tech_1.with_user(self.user_tech_1).unlink()

        # Intento por Supervisor
        with self.assertRaises(AccessError, msg="Se esperaba AccessError: el supervisor tampoco tiene permisos de eliminación física (unlink)."):
            self.maint_tech_2.with_user(self.user_super).unlink()

    def test_04_acl_technician_write_restrictions(self):
        """Validar que los técnicos no puedan crear ni modificar perfiles de técnicos en el sistema."""
        tech_env = self.env['techstore.technician'].with_user(self.user_tech_1)
        
        # Intentar modificar el nombre de otro técnico
        with self.assertRaises(AccessError, msg="Se esperaba AccessError: los técnicos no pueden editar perfiles de técnicos."):
            self.tech_rec_2.with_user(self.user_tech_1).write({'name': 'Nombre Hackeado'})

        # Intentar crear un nuevo técnico
        with self.assertRaises(AccessError, msg="Se esperaba AccessError: los técnicos no pueden crear nuevos técnicos."):
            tech_env.create({
                'name': 'Técnico Infiltrado',
                'identification': 'ID-HACK',
                'phone': '000-000'
            })
