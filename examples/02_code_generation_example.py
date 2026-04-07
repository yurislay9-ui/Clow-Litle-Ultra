#!/usr/bin/env python3
"""
Ejemplo 2: Generación de Código con Self-Healing
================================================
Este ejemplo muestra cómo Claw-Litle genera código Python automáticamente,
lo prueba en sandbox y lo autocorrige si es necesario.

Requisitos:
- Claw-Litle instalado
- Entorno virtual activado
"""

import sys
from pathlib import Path

# Agregar el proyecto al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.code_gen.template_engine import TemplateEngine
from src.code_gen.sandbox_executor import SandboxExecutor
from src.code_gen.self_healing_engine import SelfHealingEngine
from src.code_gen.buddy_reviewer import BuddyReviewer
from src.environment_detector import EnvironmentDetector


def ejemplo_generacion_simple():
    """Ejemplo básico: Generar una calculadora CLI."""
    print("\n" + "="*60)
    print("EJEMPLO 1: Generación de Código Simple")
    print("="*60)
    
    # Detectar entorno
    detector = EnvironmentDetector()
    profile = detector.detect_environment()
    print(f"\n📱 Entorno detectado: {profile['environment']['type']}")
    print(f"   RAM disponible: {profile['environment']['ram_available_mb']}MB")
    print(f"   Python: {profile['environment']['python_version']}")
    
    # Inicializar template engine
    template_engine = TemplateEngine()
    
    # Contexto del usuario
    context = {
        "app_type": "calculadora",
        "interface": "cli",
        "features": ["suma", "resta", "multiplicación", "división"],
        "storage": "none",
        "description": "Calculadora CLI con operaciones básicas"
    }
    
    print(f"\n🎯 Generando: {context['app_type']} con interfaz {context['interface']}")
    
    # Seleccionar y renderizar template
    generated_code = template_engine.generate(
        template_name="cli_app.py.template",
        context=context,
        environment_profile=profile
    )
    
    print(f"\n✅ Código generado ({len(generated_code)} caracteres):")
    print("-" * 40)
    print(generated_code[:500] + "..." if len(generated_code) > 500 else generated_code)
    print("-" * 40)
    
    return generated_code


def ejemplo_sandbox_testing():
    """Ejemplo: Ejecutar código en sandbox."""
    print("\n" + "="*60)
    print("EJEMPLO 2: Testing en Sandbox")
    print("="*60)
    
    # Código de prueba (simple y seguro)
    test_code = """
def calcular_promedio(numeros):
    '''Calcula el promedio de una lista de números.'''
    if not numeros:
        return 0
    return sum(numeros) / len(numeros)

# Test automático
if __name__ == "__main__":
    test_cases = [
        ([1, 2, 3, 4, 5], 1.0),
        ([10, 20], 15.0),
        ([], 0),
    ]
    
    for nums, expected in test_cases:
        result = calcular_promedio(nums)
        print(f"Promedio({nums}) = {result} (esperado: {expected})")
        assert abs(result - expected) < 0.01, f"Falló para {nums}"
    
    print("✅ Todos los tests pasaron!")
"""
    
    print("\n🧪 Código a testear:")
    print(test_code[:200] + "...")
    
    # Ejecutar en sandbox
    sandbox = SandboxExecutor(
        timeout=10,          # 10 segundos máx
        memory_limit=256,    # 256MB máx
        allow_network=False  # Sin red por seguridad
    )
    
    print("\n⚡ Ejecutando en sandbox...")
    result = sandbox.execute(test_code)
    
    print(f"\n📊 Resultado:")
    print(f"   Exit code: {result['exit_code']}")
    print(f"   Tiempo: {result['execution_time']:.3f}s")
    print(f"   Memoria: {result['memory_used']}MB")
    print(f"   Success: {result['success']}")
    
    if result['stdout']:
        print(f"\n📤 Output:")
        print(result['stdout'][:300])
    
    if result['stderr']:
        print(f"\n⚠️  Errores:")
        print(result['stderr'][:300])
    
    return result


def ejemplo_self_healing():
    """Ejemplo: Self-Healing cuando el código falla."""
    print("\n" + "="*60)
    print("EJEMPLO 3: Self-Healing Engine")
    print("="*60)
    
    # Código con error intencional (importa tkinter que no está disponible en Termux)
    problematic_code = """
import tkinter as tk
from tkinter import messagebox

def crear_ventana():
    root = tk.Tk()
    root.title("Mi App")
    messagebox.showinfo("Hola", "Bienvenido a mi app")
    root.mainloop()

if __name__ == "__main__":
    crear_ventana()
"""
    
    print("\n⚠️  Código problemático (usa tkinter, no disponible en Termux):")
    print(problematic_code[:200] + "...")
    
    # Inicializar self-healing engine
    healing_engine = SelfHealingEngine(
        max_iterations=3,
        timeout_per_iteration=10
    )
    
    print("\n🔧 Iniciando proceso de self-healing...")
    result = healing_engine.heal_code(
        code=problematic_code,
        environment="termux_arm64",
        error_context="ModuleNotFoundError: No module named 'tkinter'"
    )
    
    print(f"\n📊 Resultado del healing:")
    print(f"   Iteraciones: {result['iterations_used']}")
    print(f"   Success: {result['success']}")
    print(f"   Tiempo total: {result['total_time']:.2f}s")
    
    if result['success']:
        print(f"\n✅ Código corregido:")
        print("-" * 40)
        print(result['fixed_code'][:400] + "...")
        print("-" * 40)
    else:
        print(f"\n❌ No se pudo corregir el código")
        print(f"   Errores: {result.get('errors', [])}")
    
    return result


def ejemplo_buddy_review():
    """Ejemplo: Buddy Reviewer revisa código."""
    print("\n" + "="*60)
    print("EJEMPLO 4: Buddy Reviewer (Code Review)")
    print("="*60)
    
    # Código a revisar
    code_to_review = """
import os
import sqlite3

def get_user_data(user_id):
    # Conexión directa a BD
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Query vulnerable a SQL injection
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    
    result = cursor.fetchone()
    conn.close()
    return result

def execute_command(cmd):
    # PELIGROSO: ejecutar comandos del usuario
    os.system(cmd)
"""
    
    print("\n🔍 Código a revisar:")
    print(code_to_review[:300] + "...")
    
    # Inicializar buddy reviewer
    buddy = BuddyReviewer()
    
    print("\n📋 Revisando código...")
    review = buddy.review(
        code=code_to_review,
        environment="termux_arm64",
        intent="data_access"
    )
    
    print(f"\n📊 Veredicto del Buddy:")
    print(f"   Verdict: {review['verdict']}")
    print(f"   Score: {review['overall_score']:.2f}")
    print(f"   Security: {review['category_scores']['security']:.2f}")
    print(f"   Compat: {review['category_scores']['compatibility']:.2f}")
    print(f"   Quality: {review['category_scores']['quality']:.2f}")
    print(f"   Perf: {review['category_scores']['performance']:.2f}")
    
    if review['issues']:
        print(f"\n⚠️  Issues encontrados ({len(review['issues'])}):")
        for i, issue in enumerate(review['issues'], 1):
            print(f"   {i}. [{issue['severity']}] {issue['description']}")
            print(f"      Línea {issue.get('line', '?')}: {issue.get('suggestion', '')}")
    
    return review


def main():
    """Ejecutar todos los ejemplos."""
    print("\n" + "🦁 "*20)
    print(" Claw-Litle - Ejemplos de Code Generation")
    print("🦁 "*20)
    
    try:
        # Ejemplo 1: Generación simple
        ejemplo_generacion_simple()
        
        # Ejemplo 2: Sandbox testing
        ejemplo_sandbox_testing()
        
        # Ejemplo 3: Self-healing
        ejemplo_self_healing()
        
        # Ejemplo 4: Buddy review
        ejemplo_buddy_review()
        
        print("\n" + "="*60)
        print("✅ ¡Todos los ejemplos completados exitosamente!")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Ejecución cancelada por el usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()