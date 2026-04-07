#!/usr/bin/env python3
"""
Ejemplo 1: Búsqueda Web con Swarm Intelligence
==============================================
Este ejemplo muestra cómo usar Claw-Litle para realizar búsquedas web
utilizando múltiples agentes en paralelo con control térmico.

Requisitos:
- Claw-Litle instalado
- Conexión a internet
- TOKEN de Telegram configurado (opcional, solo para notificaciones)
"""

import asyncio
import sys
from pathlib import Path

# Agregar el proyecto al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.swarm_manager import SwarmManager
from src.agents.google_searcher import GoogleSearcher
from src.agents.bing_searcher import BingSearcher
from src.agents.deep_scraper import DeepScraper
from src.agents.synthesizer import Synthesizer
from src.monitoring.thermal_monitor import ThermalMonitor


async def ejemplo_busqueda_simple():
    """Ejemplo básico: Búsqueda con un solo agente."""
    print("\n" + "="*60)
    print("EJEMPLO 1: Búsqueda Simple con Google")
    print("="*60)
    
    searcher = GoogleSearcher()
    results = await searcher.search("Python asyncio tutorial", max_results=5)
    
    print(f"\n✅ Encontrados {len(results)} resultados:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.get('title', 'N/A')}")
        print(f"   URL: {result.get('url', 'N/A')}")
        print(f"   snippet: {result.get('snippet', 'N/A')[:100]}...")
    
    return results


async def ejemplo_swarm_completo():
    """Ejemplo avanzado: Swarm con múltiples agentes."""
    print("\n" + "="*60)
    print("EJEMPLO 2: Swarm Intelligence (3 Agentes)")
    print("="*60)
    
    # Inicializar monitor térmico
    thermal_monitor = ThermalMonitor()
    
    # Configurar swarm manager
    swarm = SwarmManager(
        max_concurrent_agents=2,  # Límite por thermal guard
        thermal_threshold=70,      # °C
        search_timeout=30          # segundos
    )
    
    # Agregar agentes
    swarm.add_agent("google", GoogleSearcher())
    swarm.add_agent("bing", BingSearcher())
    swarm.add_agent("deep", DeepScraper())
    
    # Query del usuario
    query = "mejores prácticas seguridad Python 2024"
    print(f"\n🔍 Query: '{query}'")
    print(f"📱 Temperatura CPU inicial: {thermal_monitor.get_temperature()}°C")
    
    # Ejecutar swarm
    results = await swarm.execute_swarm(
        query=query,
        max_results_per_agent=5
    )
    
    print(f"\n📊 Resultados recolectados:")
    print(f"   Total raw: {len(results)}")
    print(f"   Agentes usados: {swarm.get_agents_used()}")
    print(f"   Tiempo total: {swarm.get_execution_time():.2f}s")
    
    # Sintetizar resultados
    print("\n🔄 Sintetizando resultados...")
    synthesizer = Synthesizer()
    synthesis = await synthesizer.synthesize(results)
    
    print(f"\n✨ Síntesis completada:")
    print(f"   Entidades clave: {len(synthesis.get('key_findings', []))}")
    print(f"   Confidence: {synthesis.get('confidence_score', 0):.2%}")
    print(f"   Fuentes consultadas: {len(synthesis.get('sources_breakdown', {}))}")
    
    # Mostrar top findings
    print("\n📋 Top 3 Hallazgos:")
    for i, finding in enumerate(synthesis.get('key_findings', [])[:3], 1):
        print(f"\n{i}. {finding.get('entity', 'N/A')}")
        print(f"   Score: {finding.get('tfidf_score', 0):.3f}")
        print(f"   Mencionado por: {', '.join(finding.get('mentioned_by', []))}")
    
    return synthesis


async def ejemplo_busqueda_semantica():
    """Ejemplo: Búsqueda semántica local (offline)."""
    print("\n" + "="*60)
    print("EJEMPLO 3: Búsqueda Semántica Local (Offline)")
    print("="*60)
    
    from src.agents.semantic_searcher import SemanticSearcher
    
    # Inicializar buscador semántico
    semantic_searcher = SemanticSearcher()
    
    # Primero, indexar algunos documentos (simulados)
    print("\n📚 Indexando documentos locales...")
    documents = [
        "Python es un lenguaje de programación interpretado",
        "asyncio permite programación asíncrona en Python",
        "La seguridad informática es crucial en desarrollo web",
        "Los modelos ONNX son optimizados para inferencia",
        "Termux permite ejecutar Linux en Android"
    ]
    
    await semantic_searcher.index_documents(documents)
    print(f"✅ {len(documents)} documentos indexados")
    
    # Búsqueda semántica
    query = "programación asíncrona Python"
    print(f"\n🔍 Buscando: '{query}'")
    
    results = await semantic_searcher.search(query, top_k=3)
    
    print(f"\n✅ Resultados (similitud semántica):")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.get('text', 'N/A')}")
        print(f"   Score: {result.get('score', 0):.3f}")
    
    return results


async def main():
    """Ejecutar todos los ejemplos."""
    print("\n" + "🦁 "*20)
    print(" Claw-Litle - Ejemplos de Búsqueda Web")
    print("🦁 "*20)
    
    try:
        # Ejemplo 1: Búsqueda simple
        await ejemplo_busqueda_simple()
        
        # Ejemplo 2: Swarm completo
        await ejemplo_swarm_completo()
        
        # Ejemplo 3: Búsqueda semántica
        await ejemplo_busqueda_semantica()
        
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
    asyncio.run(main())