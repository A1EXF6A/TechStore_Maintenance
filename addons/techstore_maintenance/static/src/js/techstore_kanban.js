/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { KanbanController } from "@web/views/kanban/kanban_controller";
import { useService } from "@web/core/utils/hooks";

patch(KanbanController.prototype, {
    setup() {
        super.setup(...arguments);
        this.actionService = useService("action");
        this.orm = useService("orm");
    },

    async dropRecord(record, targetColumn) {
        if (this.model && this.model.root && this.model.root.resModel === 'techstore.maintenance') {
            const recordId = record.resId;
            const targetState = targetColumn.value;
            const currentState = record.data.state;

            if (currentState === targetState) {
                return;
            }

            const defaultComments = {
                'nuevo': 'Mantenimiento Creado',
                'asignado': 'Mantenimiento Asignado',
                'en_proceso': 'Mantenimiento En Proceso',
                'pendiente': 'Mantenimiento Pendiente',
                'finalizado': 'Mantenimiento Finalizado',
                'cancelado': 'Mantenimiento Cancelado'
            };
            const defaultComment = defaultComments[targetState] || 'Mantenimiento Cambiado';

            try {
                // Llamar al método Python para crear el wizard y obtener el diccionario de acción
                const action = await this.orm.call(
                    'techstore.maintenance',
                    '_open_state_wizard',
                    [[recordId], targetState, defaultComment]
                );

                // Mostrar el modal de confirmación
                await this.actionService.doAction(action, {
                    onClose: async () => {
                        // Obtener el estado actual desde la base de datos para verificar si cambió
                        const [updatedRecord] = await this.orm.read(
                            'techstore.maintenance',
                            [recordId],
                            ['state']
                        );

                        if (updatedRecord && updatedRecord.state !== currentState) {
                            // Si cambió de estado (se movió con éxito), abrir la vista formulario del mantenimiento
                            await this.actionService.doAction({
                                type: 'ir.actions.act_window',
                                res_model: 'techstore.maintenance',
                                res_id: recordId,
                                views: [[false, 'form']],
                                target: 'current',
                            });
                        } else {
                            // Si no cambió, solo recargamos el tablero
                            await this.model.root.load();
                            this.render();
                        }
                    }
                });
            } catch (error) {
                // En caso de error, recargar el tablero para asegurar consistencia
                await this.model.root.load();
                this.render();
                throw error;
            }
        } else {
            await super.dropRecord(...arguments);
        }
    }
});
