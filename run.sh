#!/bin/bash
# Script de arranque oficial para CLAW-LITE ULTRA PRO

# 1. Activar el entorno virtual
source venv/bin/activate

# 2. Navegar al directorio del subproyecto que contiene el código fuente
cd claw-lite-ultra-pro

# 3. Ejecutar el bot como un módulo desde el directorio correcto
# Esto asegura que todas las rutas relativas funcionen como se espera.
python -m src.main
