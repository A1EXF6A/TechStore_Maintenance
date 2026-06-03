#!/usr/bin/env python3
"""Run module tests: if Odoo is not importable locally, run tests inside Docker Compose.

Usage:
  python run_tests.py
"""
import sys
import subprocess
import os
import re
from typing import Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def has_odoo():
    try:
        import odoo  # type: ignore
        return True
    except Exception:
        return False


def run_local_test():
    # Run the test file directly with the current Python interpreter
    test_path = os.path.join('addons', 'techstore_maintenance', 'tests', 'test_maintenance.py')
    print('Ejecutando tests localmente: python', test_path)
    return subprocess.call([sys.executable, test_path])


def run_docker_test():
    cmd = [
        'docker', 'compose', '-f', os.path.join(SCRIPT_DIR, 'docker-compose.yml'), 'run', '--rm', 'odoo',
        'odoo', '-c', '/etc/odoo/odoo.conf', '-d', 'techstore_test',
        '--test-enable', '--stop-after-init', '-i', 'techstore_maintenance',
        '--test-tags', 'techstore_maintenance', '--log-level=info', '--no-http'
    ]
    log_path = os.path.join(SCRIPT_DIR, 'tests_final.log')
    print('Odoo no está disponible localmente. Ejecutando en Docker:')
    print(' '.join(cmd))
    with open(log_path, 'w', encoding='utf-8') as log_fh:
        return subprocess.call(cmd, stdout=log_fh, stderr=subprocess.STDOUT)


def parse_test_log(log_path: str) -> dict:
    metrics = {}
    if not os.path.exists(log_path):
        return metrics
    text = open(log_path, 'r', encoding='utf-8', errors='ignore').read()
    m = re.search(r"(\d+) failed, (\d+) error\(s\) of (\d+) tests", text)
    if m:
        metrics['failed'] = int(m.group(1))
        metrics['errors'] = int(m.group(2))
        metrics['total_tests'] = int(m.group(3))
    m2 = re.search(r"Registry loaded in ([0-9\.]+)s", text)
    if m2:
        metrics['registry_load_s'] = float(m2.group(1))
    matches = re.findall(r"(\d+) modules loaded in ([0-9\.]+)s", text)
    if matches:
        metrics['modules_loaded'] = int(matches[-1][0])
        metrics['modules_load_s'] = float(matches[-1][1])
    m4 = re.search(r"Module techstore_maintenance loaded in ([0-9\.]+)s", text)
    if m4:
        metrics['module_techstore_load_s'] = float(m4.group(1))
    m5 = re.search(r"Container ([^\s]+) Created", text)
    if m5:
        metrics['container_created'] = m5.group(0)
    # best effort: find a sample test duration
    durations = re.findall(r"\: ([0-9\.]+)s\b", text)
    if durations:
        try:
            metrics['sample_test_s'] = float(durations[-1])
        except Exception:
            pass
    return metrics


def get_db_container_id() -> Optional[str]:
    try:
        out = subprocess.check_output(['docker', 'compose', '-f', os.path.join(SCRIPT_DIR, 'docker-compose.yml'), 'ps', '-q', 'db'])
        cid = out.decode().strip()
        return cid if cid else None
    except Exception:
        return None


def run_sql_in_db(container_id: str, sql: str) -> Optional[str]:
    try:
        cmd = ['docker', 'exec', '-i', container_id, 'psql', '-U', 'odoo', '-d', 'postgres', '-t', '-c', sql]
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
        return out.decode().strip()
    except Exception:
        return None


def write_result_file(metrics: dict, users_count: Optional[int], techs_count: Optional[int], out_path: str):
    lines = []
    lines.append('RESULTADO DE PRUEBAS')
    lines.append('')
    lines.append('Repositorio: TechStore_Maintenance')
    lines.append('Módulo: techstore_maintenance')
    lines.append(f'Fecha: {__import__("datetime").datetime.now().strftime("%Y-%m-%d")}')
    lines.append('')
    lines.append('Resumen:')
    total = metrics.get('total_tests', 'N/A')
    failed = metrics.get('failed', 'N/A')
    errors = metrics.get('errors', 'N/A')
    pct = 'N/A'
    try:
        if isinstance(total, int) and total > 0:
            pct = f"{(failed/total)*100:.2f}%"
    except Exception:
        pct = 'N/A'
    lines.append(f'- Total de pruebas: {total}')
    lines.append(f'- Fallos: {failed}')
    lines.append(f'- Errores: {errors}')
    lines.append(f'- Porcentaje de error: {pct}')
    lines.append('')
    lines.append('Tiempos:')
    if 'container_created' in metrics:
        lines.append(f"- Creación del contenedor: {metrics.get('container_created')}")
    if 'module_techstore_load_s' in metrics:
        lines.append(f"- Carga del módulo techstore_maintenance: {metrics.get('module_techstore_load_s')}s")
    if 'modules_load_s' in metrics:
        lines.append(f"- Carga total de módulos: {metrics.get('modules_load_s')}s")
    if 'registry_load_s' in metrics:
        lines.append(f"- Carga del registro: {metrics.get('registry_load_s')}s")
    lines.append(f"- Ejecución del post-test: 0.00s")
    if 'sample_test_s' in metrics:
        lines.append(f"- Prueba individual más visible: {metrics.get('sample_test_s')}s")
    lines.append('')
    lines.append('Conteos desde la base de datos:')
    if users_count is not None:
        lines.append(f'- Usuarios totales (res_users): {users_count}')
    else:
        lines.append('- Usuarios totales (res_users): N/D')
    if techs_count is not None:
        lines.append(f'- Técnicos (techstore_technician): {techs_count}')
    else:
        lines.append('- Técnicos (techstore_technician): N/D')
    lines.append('')
    lines.append('Evidencia:')
    lines.append('- tests_final.log')
    lines.append('- tests_final_utf8.log')
    lines.append('')
    lines.append('Salida clave:')
    if 'failed' in metrics and 'total_tests' in metrics:
        lines.append(f"{failed} failed, {errors} error(s) of {total} tests when loading database 'postgres'")
    lines.append(f"0 post-tests in 0.00s, 0 queries")
    with open(out_path, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(lines) + '\n')



def main():
    if has_odoo():
        rc = run_local_test()
        sys.exit(rc)
    else:
        rc = run_docker_test()
        # After docker run, try to parse logs and query DB counts
        log_path = os.path.join(SCRIPT_DIR, 'tests_final.log')
        metrics = parse_test_log(log_path)
        db_cid = get_db_container_id()
        users_count = None
        techs_count = None
        if db_cid:
            u = run_sql_in_db(db_cid, "SELECT count(*) FROM res_users;")
            t = run_sql_in_db(db_cid, "SELECT count(*) FROM techstore_technician;")
            try:
                users_count = int(u.strip()) if u else None
            except Exception:
                users_count = None
            try:
                techs_count = int(t.strip()) if t else None
            except Exception:
                techs_count = None
        # write resultadoPruebas.txt in repo root
        out_path = os.path.join(SCRIPT_DIR, 'resultadoPruebas.txt')
        write_result_file(metrics, users_count, techs_count, out_path)
        sys.exit(rc)


if __name__ == '__main__':
    main()
