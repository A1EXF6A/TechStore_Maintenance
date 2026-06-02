# pyrefly: ignore [missing-import]
from odoo.tests import common
# pyrefly: ignore [missing-import]
from odoo.exceptions import ValidationError

class TestTechStoreMaintenance(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create standard specialty
        cls.specialty_hw = cls.env['techstore.specialty'].create({
            'name': 'Hardware Test'
        })
        
        # Create custom client
        cls.client_1 = cls.env['techstore.client'].create({
            'name': 'Test Client S.A.',
            'identification': '1792345678009',
            'phone': '022345678',
            'email': 'test@client.com'
        })

        # Create equipment
        # Create equipment type and equipment
        cls.equipment_type = cls.env['techstore.equipment.type'].create({'name': 'Laptop'})
        cls.equipment_1 = cls.env['techstore.equipment'].create({
            'client_id': cls.client_1.id,
            'equipment_type_id': cls.equipment_type.id,
            'brand': 'Dell',
            'model': 'Latitude',
            'serial_number': 'SN-TEST-123',
            'state': 'received'
        })

        # Create specialty and technician
        cls.technician_1 = cls.env['techstore.technician'].create({
            'name': 'Test Tech',
            'identification': '1708932452',  # Valid Modulo 10
            'phone': '0999999991',         # Valid 10-digit phone
            'email': 'tech@test.com',
            'specialty_id': cls.specialty_hw.id
        })

        # Get technician user group and create a technician user for permission tests
        cls.group_tech = cls.env.ref('techstore_maintenance.group_techstore_technician')
        cls.tech_user = cls.env['res.users'].create({
            'name': 'Tech User',
            'login': 'tech.user@test.local',
            'email': 'tech.user@test.local',
            'groups_id': [(6, 0, [cls.group_tech.id])]
        })
        cls.technician_1.user_id = cls.tech_user

    def test_01_technician_validation_valid(self):
        """Test creating a technician with valid Ecuadorian ID and Phone"""
        tech = self.env['techstore.technician'].create({
            'name': 'Valid Tech',
            'identification': '1712345675',  # Valid Ecuadorian ID
            'phone': '0999999992',         # Valid phone
            'specialty_id': self.specialty_hw.id
        })
        self.assertTrue(tech.id)

    def test_01_technician_validation_invalid_cedula(self):
        """Test that invalid Ecuadorian ID raises ValidationError"""
        with self.assertRaises(ValidationError):
            self.env['techstore.technician'].create({
                'name': 'Invalid Cedula Tech',
                'identification': '1234567890',  # Invalid Modulo 10
                'phone': '0999999999',
                'specialty_id': self.specialty_hw.id
            })

    def test_01_technician_validation_invalid_phone(self):
        """Test that invalid phone length raises ValidationError"""
        with self.assertRaises(ValidationError):
            self.env['techstore.technician'].create({
                'name': 'Invalid Phone Tech',
                'identification': '1734567892',  # Valid ID
                'phone': '1234567',             # Too short
                'specialty_id': self.specialty_hw.id
            })

    def test_02_equipment_status_sync(self):
        """Test automated equipment state transitions based on maintenance state updates"""
        # Initially equipment is received
        self.assertEqual(self.equipment_1.state, 'received')

        # Create maintenance request
        maint = self.env['techstore.maintenance'].create({
            'client_id': self.client_1.id,
            'equipment_id': self.equipment_1.id,
            'technician_id': self.technician_1.id,
            'description': 'Keyboard replacement',
            'maintenance_type': 'corrective'
        })
        
        # Linked equipment state is received
        self.assertEqual(self.equipment_1.state, 'received')

        # Change maintenance to 'en_proceso' -> equipment should be 'under_repair'
        maint.state = 'en_proceso'
        self.assertEqual(self.equipment_1.state, 'under_repair')

        # Change maintenance to 'pendiente' -> equipment remains 'under_repair'
        maint.state = 'pendiente'
        self.assertEqual(self.equipment_1.state, 'under_repair')

        # Change maintenance to 'finalizado' -> equipment should be 'repaired'
        maint.state = 'finalizado'
        self.assertEqual(self.equipment_1.state, 'repaired')

    def test_03_technician_received_only_constraint(self):
        """Test that a technician user cannot create maintenance for non-received equipment"""
        # Change equipment to 'under_repair' (not received)
        self.equipment_1.state = 'under_repair'

        # Trying to create maintenance as a technician user should raise a ValidationError
        with self.assertRaises(ValidationError):
            self.env['techstore.maintenance'].with_user(self.tech_user).create({
                'client_id': self.client_1.id,
                'equipment_id': self.equipment_1.id,
                'description': 'Attempting creation for under_repair equipment',
                'maintenance_type': 'corrective'
            })

    def test_04_equipment_physical_state_default(self):
        """Test that a newly created equipment defaults state_id to 'nuevo'"""
        state_nuevo = self.env['techstore.equipment.state'].search([('code', '=', 'nuevo')], limit=1)
        if not state_nuevo:
            state_nuevo = self.env['techstore.equipment.state'].create({
                'code': 'nuevo',
                'name': 'Nuevo'
            })

        equipment = self.env['techstore.equipment'].create({
            'client_id': self.client_1.id,
            'equipment_type_id': self.equipment_type.id,
            'brand': 'HP',
            'model': 'ProBook',
            'serial_number': 'SN-NEW-999'
        })

        self.assertEqual(equipment.state_id.id, state_nuevo.id)
        self.assertEqual(equipment.state_id.code, 'nuevo')
        self.assertEqual(equipment.state_id.name, 'Nuevo')

    def test_05_technician_cannot_modify_history(self):
        """Test that a non-admin technician user cannot directly create, write or delete history records and gets clean UserError"""
        from odoo.exceptions import UserError

        maint = self.env['techstore.maintenance'].create({
            'client_id': self.client_1.id,
            'equipment_id': self.equipment_1.id,
            'technician_id': self.technician_1.id,
            'description': 'History access check',
            'maintenance_type': 'corrective'
        })

        with self.assertRaises(UserError) as cm:
            self.env['techstore.maintenance.history'].with_user(self.tech_user).create({
                'maintenance_id': maint.id,
                'old_state': 'nuevo',
                'new_state': 'asignado',
                'comment': 'Direct hack attempt'
            })
        self.assertIn("No tienes acceso", str(cm.exception))

    def test_06_block_edit_when_finalizado_or_cancelado(self):
        """Test that a maintenance cannot be edited once it is in finalizado or cancelado status"""
        maint = self.env['techstore.maintenance'].create({
            'client_id': self.client_1.id,
            'equipment_id': self.equipment_1.id,
            'description': 'Maintenance block check',
            'maintenance_type': 'corrective'
        })

        # Transition to finalizado
        maint.state = 'finalizado'
        self.assertEqual(maint.state, 'finalizado')

        # Trying to edit description should raise a ValidationError
        with self.assertRaises(ValidationError) as cm:
            maint.write({
                'description': 'Attempting edit after completion'
            })
        self.assertIn("No se puede modificar un mantenimiento", str(cm.exception))

    def test_07_state_wizard_comment_sync(self):
        """Test that transition wizard logs customized comments into history log successfully"""
        maint = self.env['techstore.maintenance'].create({
            'client_id': self.client_1.id,
            'equipment_id': self.equipment_1.id,
            'description': 'Wizard transition test',
            'maintenance_type': 'corrective'
        })

        # Create transition wizard
        wizard = self.env['techstore.maintenance.state.wizard'].create({
            'maintenance_id': maint.id,
            'old_state': 'nuevo',
            'new_state': 'asignado',
            'comment': 'Este es un comentario de transicion personalizado'
        })

        # Confirm wizard action
        wizard.action_confirm()

        # Ensure state updated
        self.assertEqual(maint.state, 'asignado')

        # Ensure history log has the correct customized comment
        history = self.env['techstore.maintenance.history'].search([
            ('maintenance_id', '=', maint.id),
            ('new_state', '=', 'asignado')
        ], limit=1)
        self.assertTrue(history)
        self.assertEqual(history.comment, 'Este es un comentario de transicion personalizado')


