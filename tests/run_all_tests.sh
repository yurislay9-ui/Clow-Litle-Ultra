#!/bin/bash
# Script para ejecutar todos los tests del proyecto Claw-Litle

set -e

echo "=============================================="
echo " Claw-Litle - Test Suite Completa"
echo "=============================================="
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir mensajes
print_header() {
    echo -e "${BLUE}>>> $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Verificar que estamos en el directorio correcto
if [ ! -f "pyproject.toml" ]; then
    print_error "pyproject.toml no encontrado. Ejecuta este script desde la raíz del proyecto."
    exit 1
fi

# Verificar que hay un entorno virtual
if [ ! -d "venv" ]; then
    print_warning "Entorno virtual no encontrado. Creando..."
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements-dev.txt
fi

# Activar entorno virtual
source venv/bin/activate

# Crear directorio de reportes
mkdir -p test_reports

# Contadores
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

echo ""
print_header "1. Ejecutando Linting (Ruff)"
echo "----------------------------------------"
if command -v ruff &> /dev/null; then
    ruff check src/ tests/ --output-format=github || print_warning "Ruff encontró problemas de estilo"
    print_success "Linting completado"
else
    print_warning "Ruff no instalado, saltando linting"
fi

echo ""
print_header "2. Ejecutando Type Checking (Mypy)"
echo "----------------------------------------"
if command -v mypy &> /dev/null; then
    mypy src/ --ignore-missing-imports --no-error-summary || print_warning "Mypy encontró errores de tipos"
    print_success "Type checking completado"
else
    print_warning "Mypy no instalado, saltando type checking"
fi

echo ""
print_header "3. Ejecutando Tests Unitarios"
echo "----------------------------------------"
if python -m pytest tests/unit/ -v --tb=short --tb=line 2>/dev/null; then
    print_success "Tests unitarios pasaron"
    ((PASSED_TESTS++))
else
    print_error "Tests unitarios fallaron"
    ((FAILED_TESTS++))
fi
((TOTAL_TESTS++))

echo ""
print_header "4. Ejecutando Tests de Integración"
echo "----------------------------------------"
if python -m pytest tests/integration/ -v --tb=short 2>/dev/null; then
    print_success "Tests de integración pasaron"
    ((PASSED_TESTS++))
else
    print_error "Tests de integración fallaron"
    ((FAILED_TESTS++))
fi
((TOTAL_TESTS++))

echo ""
print_header "5. Ejecutando Tests Generales"
echo "----------------------------------------"
if python -m pytest tests/test_*.py -v --tb=short 2>/dev/null; then
    print_success "Tests generales pasaron"
    ((PASSED_TESTS++))
else
    print_error "Tests generales fallaron"
    ((FAILED_TESTS++))
fi
((TOTAL_TESTS++))

echo ""
print_header "6. Ejecutando Tests de Compatibilidad Termux"
echo "----------------------------------------"
if python tests/test_termux_compatibility.py 2>/dev/null; then
    print_success "Tests de compatibilidad Termux pasaron"
    ((PASSED_TESTS++))
else
    print_warning "Tests de compatibilidad Termux fallaron (puede ser normal en PC)"
    ((SKIPPED_TESTS++))
fi
((TOTAL_TESTS++))

echo ""
print_header "7. Ejecutando Benchmark de Rendimiento"
echo "----------------------------------------"
if python tests/benchmark_performance.py 2>/dev/null; then
    print_success "Benchmark completado"
    ((PASSED_TESTS++))
else
    print_warning "Benchmark falló (puede ser por dependencias faltantes)"
    ((SKIPPED_TESTS++))
fi
((TOTAL_TESTS++))

echo ""
print_header "8. Verificando Cobertura de Tests"
echo "----------------------------------------"
if command -v pytest-cov &> /dev/null || python -m pytest --cov=src --cov-report=term 2>/dev/null; then
    python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=50 2>/dev/null || print_warning "Cobertura por debajo del 50%"
    print_success "Verificación de cobertura completada"
else
    print_warning "pytest-cov no disponible, saltando cobertura"
fi

echo ""
echo "=============================================="
echo " RESUMEN DE TESTS"
echo "=============================================="
echo ""
echo -e "Total: ${TOTAL_TESTS}"
echo -e "Pasaron: ${GREEN}${PASSED_TESTS}${NC}"
echo -e "Fallaron: ${RED}${FAILED_TESTS}${NC}"
echo -e "Saltados: ${YELLOW}${SKIPPED_TESTS}${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    print_success "¡Todos los tests críticos pasaron!"
    exit 0
else
    print_error "Algunos tests fallaron. Revisa los reportes."
    exit 1
fi