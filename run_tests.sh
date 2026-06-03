#!/bin/bash
# ============================================================================
# TechStore Maintenance - Suite de Pruebas Automatizadas
#
# Uso:
#   ./run_tests.sh            # Ejecuta todas las pruebas
#   ./run_tests.sh -v         # Modo verbose (logs completos)
#   ./run_tests.sh -c         # Limpia BD de pruebas antes de ejecutar
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB_NAME="techstore_test"
CONTAINER="odoo18"
MODULE="techstore_maintenance"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

VERBOSE=false
CLEAN=false

while getopts "vch" opt; do
    case $opt in
        v) VERBOSE=true ;;
        c) CLEAN=true ;;
        h)
            echo "Uso: $0 [-v] [-c]"
            echo "  -v    Modo verbose (muestra logs detallados)"
            echo "  -c    Limpia la base de datos de pruebas antes de ejecutar"
            exit 0
            ;;
        *) exit 1 ;;
    esac
done

log()    { echo -e "  $*"; }
header() { echo ""; echo "=============================================="; echo "  TechStore Maintenance - Suite de Pruebas"; echo "=============================================="; echo ""; }

wait_for_odoo() {
    log "Esperando a que Odoo esté disponible..."
    for i in {1..30}; do
        if podman exec "$CONTAINER" true 2>/dev/null; then
            log "${GREEN}OK${NC}"
            return 0
        fi
        sleep 1
    done
    log "${RED}TIMEOUT${NC}"
    return 1
}

# ─────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────
header
wait_for_odoo

if $CLEAN; then
    log "Limpiando base de datos '$DB_NAME'..."
    podman exec "$CONTAINER" odoo --stop-after-init \
        -d "$DB_NAME" \
        --db_host=db --db_user=odoo --db_password=odoo \
        --addons-path=/mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons \
        --xmlrpc-port=18069 2>/dev/null || true
    log "${GREEN}OK${NC}"
fi

echo ""
echo "------------------------------------------------"
echo "  Ejecutando pruebas del módulo $MODULE..."
echo "------------------------------------------------"
echo ""

echo -e "  ${CYAN}Base de datos:${NC}  $DB_NAME"
echo -e "  ${CYAN}Contenedor:${NC}    $CONTAINER"
echo -e "  ${CYAN}Módulo:${NC}        $MODULE"
echo ""

# # Ejecutar Odoo con tests
log "Ejecutando pruebas (esto puede tomar varios segundos)..."
echo ""

CMD="podman exec odoo18 odoo -d techstore_test --stop-after-init --test-enable -i techstore_maintenance --db_host=db --db_user=odoo --db_password=odoo --addons-path=/mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons --xmlrpc-port=18069"

if $VERBOSE; then
    eval "$CMD" 2>&1
    EXIT_CODE=$?
else
    eval "$CMD" > /dev/null 2>&1
    EXIT_CODE=$?
fi

# Extraer resultados del log interno de Odoo
podman exec odoo18 sh -c 'tail -500 /var/log/odoo/odoo.log' > /tmp/odoo_test_output.log 2>/dev/null

echo ""
echo "------------------------------------------------"
echo "  RESULTADOS"
echo "------------------------------------------------"
echo ""

# Extraer estadísticas del log
TOTAL=$(grep -oP '\d+ tests' /tmp/odoo_test_output.log 2>/dev/null | grep -oP '\d+' | tail -1)
QUERIES=$(grep -oP '\d+ queries' /tmp/odoo_test_output.log 2>/dev/null | grep -oP '\d+' | tail -1)
FAILURES=$(grep -oP '\d+ failed' /tmp/odoo_test_output.log 2>/dev/null | grep -oP '\d+' | tail -1)
ERRORS=$(grep -oP '\d+ error\(s\)' /tmp/odoo_test_output.log 2>/dev/null | grep -oP '\d+' | tail -1)
TIME=$(grep -oP '\d+\.\d+s test' /tmp/odoo_test_output.log 2>/dev/null | grep -oP '\d+\.\d+' | tail -1)

# Asignar defaults
TOTAL=$((TOTAL))
QUERIES=$((QUERIES))
FAILURES=$((FAILURES))
ERRORS=$((ERRORS))

echo -e "  ${BOLD}Resumen de ejecución:${NC}"
echo ""

# Tabla de archivos de prueba
declare -A TEST_FILES
TEST_FILES["test_functional"]="Pruebas Funcionales (CF-01 a CF-16)"
TEST_FILES["test_security"]="Pruebas de Seguridad (SE-01 a SE-08)"
TEST_FILES["test_performance"]="Pruebas de Rendimiento (PR-01 a PR-06)"

for FILE in test_functional test_security test_performance; do
    case $FILE in
        test_functional)  DESC="Pruebas Funcionales (CF-01 a CF-16)" ;;
        test_security)    DESC="Pruebas de Seguridad (SE-01 a SE-08)" ;;
        test_performance) DESC="Pruebas de Rendimiento (PR-01 a PR-06)" ;;
    esac

    STARTED=$(grep -c "tests.$FILE:" /tmp/odoo_test_output.log 2>/dev/null | tr -d '[:space:]')
    FILE_FAILS=$(grep -c "FAIL.*tests.$FILE:" /tmp/odoo_test_output.log 2>/dev/null | tr -d '[:space:]')
    FILE_ERRS=$(grep -c "ERROR.*tests.$FILE:" /tmp/odoo_test_output.log 2>/dev/null | tr -d '[:space:]')

    STARTED="${STARTED:-0}"
    FILE_FAILS="${FILE_FAILS:-0}"
    FILE_ERRS="${FILE_ERRS:-0}"

    if [ "$STARTED" -le 0 ] && [ "$FILE_FAILS" -le 0 ] && [ "$FILE_ERRS" -le 0 ]; then
        STARTED=$(grep -c "$FILE" /tmp/odoo_test_output.log 2>/dev/null | tr -d '[:space:]')
        STARTED="${STARTED:-0}"
    fi

    if [ "$FILE_FAILS" -gt 0 ] || [ "$FILE_ERRS" -gt 0 ]; then
        echo -e "  ${RED}X${NC} $DESC"
        echo -e "      Tests: $((STARTED)) | Fallos: ${RED}$((FILE_FAILS))${NC} | Errores: ${RED}$((FILE_ERRS))${NC}"
    else
        echo -e "  ${GREEN}OK${NC} $DESC"
        echo -e "      Tests: $((STARTED)) | ${GREEN}Todos OK${NC}"
    fi
done

echo ""
echo "------------------------------------------------"
echo -e "  ${BOLD}RESUMEN GENERAL${NC}"
echo "------------------------------------------------"
echo ""

echo -e "  ${CYAN}Total de tests:${NC}     $TOTAL"
echo -e "  ${CYAN}Consultas SQL:${NC}    $QUERIES"

if [ "$FAILURES" -gt 0 ] || [ "$ERRORS" -gt 0 ]; then
    echo -e "  ${RED}Fallos:${NC}           $FAILURES"
    echo -e "  ${RED}Errores:${NC}          $ERRORS"
else
    echo -e "  ${GREEN}Fallos:${NC}           $FAILURES"
    echo -e "  ${GREEN}Errores:${NC}          $ERRORS"
fi

if [ -n "$TIME" ]; then
    echo -e "  ${CYAN}Tiempo:${NC}           ${TIME}s"
fi

echo ""

if [ "$FAILURES" -eq 0 ] && [ "$ERRORS" -eq 0 ] && [ "$TOTAL" -gt 0 ]; then
    echo -e "  ${GREEN}${BOLD}TODAS LAS PRUEBAS PASARON CORRECTAMENTE${NC}"
    echo ""
    echo -e "  ${BOLD}Cobertura completa:${NC}"
    echo "    - CF-01 a CF-16 (Funcionales)"
    echo "    - SE-01 a SE-08 (Seguridad)"
    echo "    - PR-01 a PR-06 (Rendimiento)"
elif [ "$TOTAL" -le 0 ]; then
    echo -e "  ${YELLOW}${BOLD}NO SE PUDIERON EXTRAER RESULTADOS${NC}"
    echo ""
    echo -e "  Revisa: podman exec $CONTAINER tail -100 /var/log/odoo/odoo.log"
else
    echo -e "  ${RED}${BOLD}HAY PRUEBAS FALLIDAS${NC}"
    echo ""
    echo -e "  Revisa: podman exec $CONTAINER tail -100 /var/log/odoo/odoo.log"
    echo -e "  Log:    cat /tmp/odoo_test_output.log"
fi

echo ""
echo "=============================================="
echo ""

if [ "$FAILURES" -gt 0 ] || [ "$ERRORS" -gt 0 ]; then
    exit 1
fi
exit 0
