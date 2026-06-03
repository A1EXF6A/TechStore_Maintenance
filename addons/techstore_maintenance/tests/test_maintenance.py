# pyrefly: ignore [missing-import]
from odoo.tests import common
from odoo import fields
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
            'state': 'received',
            'problem_description': 'Pantalla parpadea intermitentemente'
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
        maint.write({
            'diagnosis': 'El teclado está dañado.',
            'solution': 'Se reemplazó el teclado por uno nuevo.',
            'estimated_cost': 45.0,
            'final_cost': 50.0,
            'state': 'finalizado'
        })
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
            'serial_number': 'SN-NEW-999',
            'problem_description': 'Batería no carga'
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
        maint.write({
            'diagnosis': 'Problema con la pantalla.',
            'solution': 'Se ajustaron los cables internos.',
            'estimated_cost': 25.0,
            'final_cost': 25.0,
            'state': 'finalizado'
        })
        self.assertEqual(maint.state, 'finalizado')

        # Trying to edit description should raise a ValidationError
        with self.assertRaises(ValidationError) as cm:
            maint.with_user(self.tech_user).write({
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

    def test_08_cannot_start_without_technician(self):
        """Test that transitioning to 'en_proceso' without an assigned technician raises ValidationError"""
        maint = self.env['techstore.maintenance'].create({
            'client_id': self.client_1.id,
            'equipment_id': self.equipment_1.id,
            'description': 'Process start without tech check',
            'maintenance_type': 'corrective'
        })
        
        # Transitioning to 'en_proceso' directly should raise ValidationError
        with self.assertRaises(ValidationError):
            maint.state = 'en_proceso'

        # Opening state wizard for 'en_proceso' should also raise ValidationError
        with self.assertRaises(ValidationError):
            maint._open_state_wizard('en_proceso', 'Mantenimiento En Proceso')

    def test_09_validation_finalizado_missing_fields(self):
        """Test that transitioning to 'finalizado' without diagnosis or solution raises ValidationError"""
        maint = self.env['techstore.maintenance'].create({
            'client_id': self.client_1.id,
            'equipment_id': self.equipment_1.id,
            'description': 'Validation missing fields check',
            'maintenance_type': 'corrective',
            'estimated_cost': 100.0,
            'final_cost': 120.0,
        })
        # Try to transition to finalizado without diagnosis and solution
        with self.assertRaises(ValidationError):
            maint.state = 'finalizado'

        # Set diagnosis but leave solution empty
        maint.diagnosis = 'Diagnóstico de prueba'
        with self.assertRaises(ValidationError):
            maint.state = 'finalizado'

        # Set solution but clear diagnosis
        maint.diagnosis = False
        maint.solution = 'Solución de prueba'
        with self.assertRaises(ValidationError):
            maint.state = 'finalizado'

    def test_10_validation_finalizado_zero_costs(self):
        """Test that transitioning to 'finalizado' with zero estimated or final cost raises ValidationError"""
        maint = self.env['techstore.maintenance'].create({
            'client_id': self.client_1.id,
            'equipment_id': self.equipment_1.id,
            'description': 'Validation zero costs check',
            'maintenance_type': 'corrective',
            'diagnosis': 'Diagnóstico de prueba',
            'solution': 'Solución de prueba',
        })
        # Try to transition to finalizado with both costs as 0
        with self.assertRaises(ValidationError):
            maint.state = 'finalizado'

        # Set estimated_cost, final_cost remains 0
        maint.estimated_cost = 50.0
        with self.assertRaises(ValidationError):
            maint.state = 'finalizado'

        # Set final_cost, estimated_cost set to 0
        maint.estimated_cost = 0.0
        maint.final_cost = 60.0
        with self.assertRaises(ValidationError):
            maint.state = 'finalizado'

    def test_11_validation_finalizado_success(self):
        """Test that transitioning to 'finalizado' succeeds when all fields and non-zero costs are provided"""
        maint = self.env['techstore.maintenance'].create({
            'client_id': self.client_1.id,
            'equipment_id': self.equipment_1.id,
            'description': 'Validation success check',
            'maintenance_type': 'corrective',
        })
        # Try to transition with everything correctly set
        maint.write({
            'diagnosis': 'Diagnóstico válido',
            'solution': 'Solución válida',
            'estimated_cost': 100.0,
            'final_cost': 100.0,
            'state': 'finalizado'
        })
        self.assertEqual(maint.state, 'finalizado')

    def test_12_equipment_problem_description_required(self):
        """Test that creating an equipment without problem_description raises ValidationError"""
        with self.assertRaises(ValidationError):
            self.env['techstore.equipment'].create({
                'client_id': self.client_1.id,
                'equipment_type_id': self.equipment_type.id,
                'brand': 'HP',
                'model': 'EliteBook',
                'serial_number': 'SN-REQ-DESC-999'
            })

    def test_13_maintenance_auto_copy_problem_description(self):
        """Test that maintenance request automatically copies problem_description from equipment"""
        equipment = self.env['techstore.equipment'].create({
            'client_id': self.client_1.id,
            'equipment_type_id': self.equipment_type.id,
            'brand': 'Asus',
            'model': 'Zenbook',
            'serial_number': 'SN-COPY-999',
            'problem_description': 'Sobrecalentamiento del procesador'
        })
        
        # Test creation auto-copy when description is not provided
        maint_create = self.env['techstore.maintenance'].create({
            'client_id': self.client_1.id,
            'equipment_id': equipment.id,
            'maintenance_type': 'corrective',
        })
        self.assertEqual(maint_create.description, 'Sobrecalentamiento del procesador')

        # Test onchange copy in user interface simulator
        maint_onchange = self.env['techstore.maintenance'].new({
            'client_id': self.client_1.id,
        })
        maint_onchange.equipment_id = equipment
        maint_onchange._onchange_equipment_id()
        self.assertEqual(maint_onchange.description, 'Sobrecalentamiento del procesador')

    def test_14_validation_finalizado_invalid_end_date_past(self):
        """Test that transitioning to 'finalizado' with a past end_date raises ValidationError"""
        from datetime import timedelta
        past_date = fields.Datetime.to_string(fields.Datetime.now() - timedelta(days=2))
        maint = self.env['techstore.maintenance'].create({
            'client_id': self.client_1.id,
            'equipment_id': self.equipment_1.id,
            'description': 'Validation past end_date check',
            'maintenance_type': 'corrective',
            'diagnosis': 'Diagnóstico válido',
            'solution': 'Solución válido',
            'estimated_cost': 10.0,
            'final_cost': 10.0,
            'end_date': past_date
        })
        with self.assertRaises(ValidationError) as cm:
            maint.state = 'finalizado'
        self.assertIn("La fecha de fin no puede ser una fecha pasada", str(cm.exception))

    def test_15_validation_finalizado_invalid_end_date_before_start(self):
        """Test that transitioning to 'finalizado' with end_date before start_date raises ValidationError"""
        from datetime import timedelta
        now = fields.Datetime.now()
        start = now + timedelta(days=2)
        end = now + timedelta(days=1)
        maint = self.env['techstore.maintenance'].create({
            'client_id': self.client_1.id,
            'equipment_id': self.equipment_1.id,
            'description': 'Validation end_date before start_date check',
            'maintenance_type': 'corrective',
            'diagnosis': 'Diagnóstico válido',
            'solution': 'Solución válido',
            'estimated_cost': 10.0,
            'final_cost': 10.0,
            'start_date': start,
            'end_date': end
        })
        with self.assertRaises(ValidationError) as cm:
            maint.state = 'finalizado'
        self.assertIn("La fecha de fin no puede ser anterior a la fecha de inicio", str(cm.exception))

    def test_16_block_edit_end_date_when_finalizado(self):
        """Test that modifying end_date is blocked once maintenance is finalized"""
        maint = self.env['techstore.maintenance'].create({
            'client_id': self.client_1.id,
            'equipment_id': self.equipment_1.id,
            'description': 'Validation block end_date check',
            'maintenance_type': 'corrective',
        })
        # Transition to finalizado with valid inputs
        maint.write({
            'diagnosis': 'Diagnóstico de prueba',
            'solution': 'Solución de prueba',
            'estimated_cost': 50.0,
            'final_cost': 50.0,
            'state': 'finalizado'
        })
        # Try to modify end_date as technician user - should raise ValidationError
        with self.assertRaises(ValidationError) as cm:
            maint.with_user(self.tech_user).write({
                'end_date': fields.Datetime.now()
            })
        self.assertIn("No se puede modificar un mantenimiento", str(cm.exception))

    def test_17_technician_readonly_field(self):
        """Test that is_technician_readonly computed field is True for technician and False for admin"""
        maint_tech = self.env['techstore.maintenance'].with_user(self.tech_user).create({
            'client_id': self.client_1.id,
            'equipment_id': self.equipment_1.id,
            'description': 'Tech readonly field check'
        })
        self.assertTrue(maint_tech.is_technician_readonly)

        maint_admin = self.env['techstore.maintenance'].create({
            'client_id': self.client_1.id,
            'equipment_id': self.equipment_1.id,
            'description': 'Admin readonly field check'
        })
        self.assertFalse(maint_admin.is_technician_readonly)

    def test_18_technician_state_change_restriction(self):
        """Test that a technician can only transition the state of maintenance requests assigned to them"""
        # Create another technician and user
        tech_2 = self.env['techstore.technician'].create({
            'name': 'Second Tech',
            'identification': '1710034065', # Valid Ecuadorian ID
            'phone': '0999999993',
            'email': 'tech2@test.com',
            'specialty_id': self.specialty_hw.id
        })
        tech_user_2 = self.env['res.users'].create({
            'name': 'Tech User 2',
            'login': 'tech.user2@test.local',
            'email': 'tech.user2@test.local',
            'groups_id': [(6, 0, [self.group_tech.id])]
        })
        tech_2.user_id = tech_user_2

        # Maintenance assigned to technician 1 (self.tech_user)
        maint_my = self.env['techstore.maintenance'].create({
            'client_id': self.client_1.id,
            'equipment_id': self.equipment_1.id,
            'technician_id': self.technician_1.id,
            'description': 'My assigned maintenance'
        })

        # Maintenance assigned to technician 2
        maint_other = self.env['techstore.maintenance'].create({
            'client_id': self.client_1.id,
            'equipment_id': self.equipment_1.id,
            'technician_id': tech_2.id,
            'description': 'Other assigned maintenance'
        })

        # Technician 1 changes state of their OWN maintenance -> should succeed
        maint_my.with_user(self.tech_user).write({'state': 'en_proceso'})
        self.assertEqual(maint_my.state, 'en_proceso')

        # Technician 1 attempts to change state of ANOTHER technician's maintenance -> should raise ValidationError
        with self.assertRaises(ValidationError) as cm:
            maint_other.with_user(self.tech_user).write({'state': 'en_proceso'})
        self.assertIn("Solo puede cambiar el estado de los mantenimientos que tiene asignados", str(cm.exception))

        # Admin changes state of other maintenance -> should succeed (admin has global access)
        maint_other.write({'state': 'en_proceso'})
        self.assertEqual(maint_other.state, 'en_proceso')

    def test_19_technician_created_maintenance_flow(self):
        """Test that a technician can create a maintenance and transition it to other states"""
        # Create maintenance request as technician user
        maint = self.env['techstore.maintenance'].with_user(self.tech_user).create({
            'client_id': self.client_1.id,
            'equipment_id': self.equipment_1.id,
            'description': 'Creado por técnico',
            'maintenance_type': 'corrective'
        })
        # Check initial state and auto-assigned technician
        self.assertEqual(maint.state, 'nuevo')
        self.assertEqual(maint.technician_id.id, self.technician_1.id)

        # Start the process
        action = maint.with_user(self.tech_user).action_to_en_proceso()
        self.assertEqual(action.get('res_model'), 'techstore.maintenance.state.wizard')
        wizard = self.env['techstore.maintenance.state.wizard'].with_user(self.tech_user).browse(action.get('res_id'))
        
        # Confirm wizard to transition to 'en_proceso'
        wizard.action_confirm()
        self.assertEqual(maint.state, 'en_proceso')

        # Move to 'pendiente'
        action_pend = maint.with_user(self.tech_user).action_to_pendiente()
        self.assertEqual(action_pend.get('res_model'), 'techstore.maintenance.state.wizard')
        wizard_pend = self.env['techstore.maintenance.state.wizard'].with_user(self.tech_user).browse(action_pend.get('res_id'))
        wizard_pend.action_confirm()
        self.assertEqual(maint.state, 'pendiente')

        # Move back to 'en_proceso'
        action_proc = maint.with_user(self.tech_user).action_to_en_proceso()
        wizard_proc = self.env['techstore.maintenance.state.wizard'].with_user(self.tech_user).browse(action_proc.get('res_id'))
        wizard_proc.action_confirm()
        self.assertEqual(maint.state, 'en_proceso')

        # Finally transition to 'finalizado'
        # First write mandatory fields for finalización
        maint.with_user(self.tech_user).write({
            'diagnosis': 'Diagnóstico de prueba',
            'solution': 'Solución de prueba',
            'estimated_cost': 50.0,
            'final_cost': 60.0
        })
        action_fin = maint.with_user(self.tech_user).action_to_finalizado()
        self.assertEqual(action_fin.get('res_model'), 'techstore.maintenance.state.wizard')
        wizard_fin = self.env['techstore.maintenance.state.wizard'].with_user(self.tech_user).browse(action_fin.get('res_id'))
        wizard_fin.action_confirm()
        self.assertEqual(maint.state, 'finalizado')




