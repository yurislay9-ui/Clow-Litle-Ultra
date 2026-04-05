#!/bin/bash
# Script de arranque oficial para CLAW-LITE ULTRA PRO v2
# Corrige el orden de activación para reflejar la estructura del proyecto.

# Nos aseguramos de que el script se ejecute desde su propio directorio
cd "$(dirname "$0")"

# 1. Navegar al directorio del subproyecto.
cd claw-lite-ultra-pro

# 2. Activar el entorno virtual que está DENTRO de este subdirectorio.
source venv/bin/activate

# 3. Ejecutar el bot como un módulo.
# Ahora estamos en el directorio correcto y el venv está activo.
python -m src.main
