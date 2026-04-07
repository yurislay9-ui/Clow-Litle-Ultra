# 📚 Ejemplos de Uso - Claw-Litle

Esta carpeta contiene ejemplos prácticos que demuestran las principales capacidades de Claw-Litle.

## 🎯 Objetivos

- Mostrar casos de uso reales
- Servir como punto de partida para desarrolladores
- Demostrar la integración entre componentes
- Proporcionar código de referencia probado

## 📁 Ejemplos Disponibles

### 1. Búsqueda Web con Swarm Intelligence (`01_web_search_example.py`)

**Descripción**: Demuestra cómo usar el sistema multi-agente para búsquedas web inteligentes.

**Conceptos demostrados**:
- Swarm Manager con control térmico
- Múltiples agentes de búsqueda (Google, Bing, Deep Scraper)
- Synthesizer con TF-IDF + consenso semántico
- Búsqueda semántica local (offline)

**Ejecutar**:
```bash
python examples/01_web_search_example.py
```

**Requisitos**:
- Conexión a internet (para búsqueda web)
- Modelo ONNX descargado (para búsqueda semántica)

---

### 2. Generación de Código con Self-Healing (`02_code_generation_example.py`)

**Descripción**: Muestra cómo Claw-Litle genera código Python, lo prueba en sandbox y lo autocorrige.

**Conceptos demostrados**:
- Template Engine (selección y renderizado)
- Sandbox Executor (ejecución segura)
- Self-Healing Engine (autocorrección)
- Buddy Reviewer (code review automático)

**Ejecutar**:
```bash
python examples/02_code_generation_example.py
```

**Requisitos**:
- Entorno virtual activado
- No requiere internet (todo es local)

---

### 3. Vision Agency (Próximamente)

**Descripción**: Demostrará cómo usar la Vision Agency para interactuar con otras apps.

**Conceptos a demostrar**:
- Permission Manager
- Screen Capture (ADB/Accessibility)
- UI Parser
- Action Planner & Executor
- PII Detector

---

### 4. Task System (Próximamente)

**Descripción**: Ejemplos de tareas programadas y workflows complejos.

**Conceptos a demostrar**:
- Task Manager (CRUD de tareas)
- Scheduler (programación cron)
- Workflow Engine (dependencias entre tareas)

---

## 🚀 Cómo Ejecutar los Ejemplos

### Opción 1: Desde la raíz del proyecto

```bash
cd claw-litle
python examples/01_web_search_example.py
```

### Opción 2: Como módulo Python

```bash
cd claw-litle
python -m examples.01_web_search_example
```

### Opción 3: En Termux (Android)

```bash
# Asumiendo que ya instalaste el proyecto
cd ~/claw-litle
source venv/bin/activate
python examples/01_web_search_example.py
```

## 📝 Estructura de un Ejemplo

Cada ejemplo sigue esta estructura:

```python
#!/usr/bin/env python3
"""
Título del Ejemplo
==================
Descripción detallada.

Requisitos:
- Lista de requisitos
"""

import sys
from pathlib import Path

# Agregar proyecto al path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Imports del proyecto
from src.modulo import Clase

def main():
    """Función principal."""
    # Código del ejemplo
    pass

if __name__ == "__main__":
    main()
```

## 🛠️ Creando Tus Propios Ejemplos

Si quieres contribuir con nuevos ejemplos:

1. **Copia la plantilla** de un ejemplo existente
2. **Sigue las convenciones**:
   - Nombres descriptivos: `03_vision_agency_example.py`
   - Documentación completa en el docstring
   - Manejo de errores con try/except
   - Prints informativos con emojis
3. **Prueba en Termux** (al menos una vez)
4. **Envía un PR** siguiendo `CONTRIBUTING.md`

## 📊 Métricas de los Ejemplos

| Ejemplo | Líneas de Código | Tiempo Ejecución | RAM Peak | Requiere Internet |
|---------|------------------|------------------|----------|-------------------|
| 01_web_search | ~150 | ~15-30s | ~150MB | ✅ Sí |
| 02_code_gen | ~200 | ~5-10s | ~120MB | ❌ No |

## ⚠️ Advertencias

- **No ejecutar en producción**: Los ejemplos son para desarrollo/testing
- **Consumo de datos**: Los ejemplos de búsqueda web consumen datos móviles
- **Permisos**: Algunos ejemplos pueden requerir permisos especiales en Android
- **Temperature**: Monitorea la temperatura en dispositivos móviles durante ejecución prolongada

## 🆘 Solución de Problemas

### Error: "Module not found"
```bash
# Asegúrate de estar en la raíz del proyecto
cd claw-litle

# O agrega el path manualmente
export PYTHONPATH=$(pwd)
```

### Error: "No module named 'src'"
```bash
# Ejecuta desde la raíz del proyecto
python examples/01_web_search_example.py
```

### Error: "ONNX model not found"
```bash
# Descarga el modelo
python scripts/download_models.py
```

### Error: "Permission denied" (Termux)
```bash
# Otorga permisos de almacenamiento
termux-setup-storage
```

## 📚 Recursos Adicionales

- [Documentación Principal](../docs/)
- [API Reference](../docs/api-reference.md)
- [Guía de Instalación](../docs/installation.md)
- [Contributing Guide](../CONTRIBUTING.md)

---

**¿Tienes preguntas o sugerencias?** Abre un issue en GitHub o únete a nuestra comunidad en Telegram.