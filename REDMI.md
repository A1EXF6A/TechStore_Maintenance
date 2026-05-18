TechStore Maintenance — Project Summary

Overview
- TechStore Maintenance: Odoo 18 module for managing technical maintenance requests, technicians, equipment, and metrics.
- Module located at: [addons/techstore_maintenance/__manifest__.py](addons/techstore_maintenance/__manifest__.py)

Quick Start (Docker)
- Uses `docker-compose.yml` to run PostgreSQL and Odoo 18.
- Start the stack:

  ```bash
  docker-compose up -d
  ```

- Odoo will be exposed on port `8069` (XML-RPC web UI). Configuration is mounted from: [config/odoo.conf](config/odoo.conf)

Module Purpose & Features
- Manage equipment inventory and intake (`techstore.equipment`). See views: [addons/techstore_maintenance/views/equipment_views.xml](addons/techstore_maintenance/views/equipment_views.xml)
- Create and track maintenance requests (`techstore.maintenance`) with lifecycle states, history, technician assignment: [addons/techstore_maintenance/models/maintenance.py](addons/techstore_maintenance/models/maintenance.py)
- Technicians model with workload and validations: [addons/techstore_maintenance/models/technician.py](addons/techstore_maintenance/models/technician.py)
- Metrics/reporting model for SLA, resolution time, and quality: [addons/techstore_maintenance/models/metrics.py](addons/techstore_maintenance/models/metrics.py)
- UI: kanban, list, form, graph and pivot views in [addons/techstore_maintenance/views/](addons/techstore_maintenance/views/)

Data & Demo
- Initial data CSVs are provided under: [addons/techstore_maintenance/data/](addons/techstore_maintenance/data/)
  - `res.partner.csv` (clients)
  - `techstore.technician.csv` (technicians)
  - `techstore.equipment.csv` (equipments)
  - `techstore.maintenance.csv` (maintenance records)

Translations
- Translation tooling script: [translate.py](translate.py)
- Spanish PO available: [addons/techstore_maintenance/i18n/es.po](addons/techstore_maintenance/i18n/es.po)

Configuration
- Odoo conf: [config/odoo.conf](config/odoo.conf)
  - DB connection: `db_host=db`, `db_user=odoo`, `db_password=odoo`
  - Addons path includes `/mnt/extra-addons` (mapped to project's `./addons`)

How to install the module in Odoo (quick)
- Start containers (`docker-compose up -d`).
- Login to Odoo at `http://localhost:8069` as admin (use `admin_passwd` in `config/odoo.conf`).
- Update Apps list and install `TechStore Maintenance` (module slug `techstore_maintenance`).

Developer notes
- Sequence data and security defined in `data/sequence_data.xml` and `security/`.
- Business logic lives in `addons/techstore_maintenance/models/`.
- Views are in `addons/techstore_maintenance/views/` and menus in `menus.xml`.
- Add unit/behavior tests (none included).

Project Files of Interest
- Compose: [docker-compose.yml](docker-compose.yml)
- Odoo config: [config/odoo.conf](config/odoo.conf)
- Module manifest: [addons/techstore_maintenance/__manifest__.py](addons/techstore_maintenance/__manifest__.py)
- Models: [addons/techstore_maintenance/models/](addons/techstore_maintenance/models/)
- Views: [addons/techstore_maintenance/views/](addons/techstore_maintenance/views/)
- Data: [addons/techstore_maintenance/data/](addons/techstore_maintenance/data/)
- i18n: [addons/techstore_maintenance/i18n/](addons/techstore_maintenance/i18n/)
- Workshop instructions: [taller_instructions.txt](taller_instructions.txt)

Potential Improvements / To Do
- Add unit and integration tests for models and metrics computation.
- Add automated CI to run linting and tests.
- Harden input validation and error handling on key write paths.
- Add scheduled jobs or triggers to keep `techstore.maintenance.metrics` in sync where needed.

Contact / Next steps
- Tell me if you want: install help, tests scaffold, or a polished README.md.
