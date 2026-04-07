# 🤝 Guía de Contribución - Claw-Litle

¡Gracias por tu interés en contribuir a Claw-Litle! Esta guía te ayudará a comenzar.

## 📋 Tabla de Contenidos
- [Código de Conducta](#código-de-conducta)
- [Cómo Contribuir](#cómo-contribuir)
- [Configuración del Entorno de Desarrollo](#configuración-del-entorno-de-desarrollo)
- [Estándares de Código](#estándares-de-código)
- [Proceso de Pull Request](#proceso-de-pull-request)
- [Testing](#testing)

## 🎯 Código de Conducta

### Nuestros Estándares
- **Mobile-First**: Todo código debe funcionar en Termux/Android
- **Privacidad**: Nunca agregues código que envíe datos sin consentimiento
- **Rendimiento**: Optimiza para dispositivos con recursos limitados (<350MB RAM)
- **Respeto**: Sé constructivo y profesional en todas las interacciones

### Comportamientos Inaceptables
- ❌ Código que requiere Docker/proot (no mobile-friendly)
- ❌ Librerías que no funcionan en ARM64/Termux
- ❌ Hardcodear secrets o credenciales
- ❌ Ignorar los límites de recursos móviles

## 🚀 Cómo Contribuir

### Tipos de Contribuciones
1. **🐛 Bug Fixes**: Corrige errores reportados
2. **✨ Nuevas Features**: Agrega funcionalidades alineadas con los 12 pilares
3. **📝 Documentación**: Mejora docs, ejemplos, tutoriales
4. **⚡ Performance**: Optimiza para móviles
5. **🧪 Tests**: Agrega o mejora cobertura de tests
6. **🔧 Refactoring**: Mejora código existente

### Flujo de Trabajo Recomendado
1. **Busca issues existentes** o crea uno nuevo
2. **Fork** el repositorio
3. **Crea una rama** (`git checkout -b feature/mi-feature`)
4. **Desarrolla y prueba** localmente
5. **Commit** con mensajes descriptivos
6. **Push** a tu fork
7. **Abre un Pull Request**

## 💻 Configuración del Entorno de Desarrollo

### Requisitos Mínimos
- Python 3.11+
- Git
- 2GB RAM libre
- 500MB espacio en disco

### Setup en Laptop/PC (Desarrollo)
```bash
# 1. Clonar repositorio
git clone https://github.com/tu-usuario/claw-litle.git
cd claw-litle

# 2. Crear entorno virtual
python -m venv venv

# 3. Activar entorno
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 4. Instalar dependencias de desarrollo
pip install -r requirements-dev.txt

# 5. Instalar herramientas de calidad
pip install ruff black mypy pre-commit

# 6. Configurar pre-commit hooks
pre-commit install

# 7. Descargar modelos (primera vez)
python scripts/download_models.py
```

### Setup en Termux (Testing Mobile)
```bash
# 1. Instalar Termux desde F-Droid
# 2. Actualizar paquetes
pkg update && pkg upgrade

# 3. Instalar Python y herramientas
pkg install python git clang

# 4. Clonar repositorio
git clone https://github.com/tu-usuario/claw-litle.git
cd claw-litle

# 5. Crear entorno virtual
python -m venv venv
source venv/bin/activate

# 6. Instalar dependencias (versión ligera)
pip install -r requirements-termux.txt

# 7. Descargar modelos
python scripts/download_models.py
```

## 📏 Estándares de Código

### Estilo y Formato
- **Python**: PEP 8
- **Type Hints**: Obligatorio en funciones nuevas
- **Formato**: Black (automático con pre-commit)
- **Linting**: Ruff
- **Type Checking**: Mypy

### Ejemplo de Código Aceptable
```python
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

def process_query(
    query: str, 
    max_results: int = 10
) -> List[Dict[str, str]]:
    """
    Procesa una query de búsqueda.
    
    Args:
        query: Texto de búsqueda
        max_results: Máximo resultados a retornar
        
    Returns:
        Lista de diccionarios con resultados
        
    Raises:
        ValueError: Si query está vacía
    """
    if not query.strip():
        raise ValueError("Query no puede estar vacía")
    
    # Implementación mobile-optimized
    results = []
    # ... código ...
    
    return results
```

### Reglas Específicas Mobile
```python
# ✅ CORRECTO: Compatible con Termux
from rich.console import Console
import sqlite3

# ❌ INCORRECTO: No disponible en Termux
import tkinter  # No hay display server
import cv2      # Problemas de compilación ARM64
```

### Límites de Recursos
```python
# ✅ CORRECTO: Lazy loading de modelos pesados
class SemanticEngine:
    def __init__(self):
        self._model = None
    
    @property
    def model(self):
        if self._model is None:
            # Cargar solo cuando se necesita
            self._model = load_onnx_model()
        return self._model

# ❌ INCORRECTO: Carga todo en memoria
class BadEngine:
    def __init__(self):
        self.model = load_onnx_model()  # 80MB inmediatamente
        self.cache = {}  # Sin límites
```

## 🧪 Testing

### Ejecutar Tests
```bash
# Tests unitarios
pytest tests/unit/ -v

# Tests de integración
pytest tests/integration/ -v

# Coverage
pytest --cov=src --cov-report=html

# Tests específicos para Termux
pytest tests/ -k "termux" -v
```

### Escribir Tests
```python
import pytest
from src.engine.nivel_1_regex import RegexEngine

def test_regex_simple_match():
    """Test que el regex engine matchea patrones simples."""
    engine = RegexEngine()
    result = engine.match("abrir chrome", "abrir")
    assert result.confidence > 0.95
    assert result.intent == "open_application"

@pytest.mark.termux
def test_mobile_compatibility():
    """Test que funciona en entorno mobile."""
    # Verificar que no usa librerías incompatibles
    import importlib
    with pytest.raises(ImportError):
        importlib.import_module("tkinter")
```

## 🔄 Proceso de Pull Request

### Antes de Enviar
1. ✅ Tests pasan localmente
2. ✅ Linting sin errores (`ruff check src/`)
3. ✅ Formato correcto (`black src/`)
4. ✅ Type hints agregados
5. ✅ Documentación actualizada
6. ✅ Ejemplos probados en Termux (si aplica)

### Template de PR
Usa el template provisto en `.github/PULL_REQUEST_TEMPLATE.md`

### Review Process
1. **CI/CD**: GitHub Actions ejecuta tests automáticamente
2. **Review**: Al menos 1 maintainer debe aprobar
3. **Cambios**: Responde a feedback y actualiza el PR
4. **Merge**: Se hace squash merge a main/develop

## 📚 Recursos Útiles

### Documentación
- [Arquitectura del Sistema](docs/architecture.md)
- [API Reference](docs/api-reference.md)
- [Guía de Instalación](docs/installation.md)
- [Security Model](docs/security.md)

### Enlaces Externos
- [Python PEP 8](https://peps.python.org/pep-0008/)
- [Termux Wiki](https://wiki.termux.com/)
- [ONNX Runtime](https://onnxruntime.ai/)

## 🆘 ¿Necesitas Ayuda?

- **Issues**: [GitHub Issues](https://github.com/tu-usuario/claw-litle/issues)
- **Discusión**: [GitHub Discussions](https://github.com/tu-usuario/claw-litle/discussions)
- **Telegram**: [Comunidad (link)](https://t.me/claw_lite_community)

## 🎖️ Reconocimientos

Los contribuidores serán reconocidos en:
- `README.md` (sección Contributors)
- `CHANGELOG.md` (cada release)
- Releases de GitHub

¡Gracias por hacer de Claw-Litle un proyecto mejor! 🚀