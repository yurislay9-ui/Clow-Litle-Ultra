#!/usr/bin/env python3
"""
Benchmark de Rendimiento para Claw-Litle.
Mide: tiempos de respuesta, uso de RAM, CPU, y límites térmicos.
"""

import time
import sys
import os
import psutil
import asyncio
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class BenchmarkResult:
    """Resultado de un benchmark."""
    name: str
    execution_time: float  # segundos
    memory_used: int  # MB
    memory_peak: int  # MB
    success: bool
    error: str = ""


class PerformanceBenchmark:
    """Clase para ejecutar benchmarks de rendimiento."""
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.results: List[BenchmarkResult] = []
    
    def get_memory_mb(self) -> int:
        """Obtiene memoria usada en MB."""
        return self.process.memory_info().rss // (1024 * 1024)
    
    def measure_function(self, name: str, func, *args, **kwargs) -> BenchmarkResult:
        """Mide el rendimiento de una función."""
        # Memoria inicial
        mem_before = self.get_memory_mb()
        mem_peak = mem_before
        
        # Medir tiempo
        start_time = time.time()
        success = True
        error = ""
        
        try:
            if asyncio.iscoroutinefunction(func):
                asyncio.run(func(*args, **kwargs))
            else:
                func(*args, **kwargs)
        except Exception as e:
            success = False
            error = str(e)
        
        execution_time = time.time() - start_time
        
        # Memoria final y peak
        mem_after = self.get_memory_mb()
        mem_used = mem_after - mem_before
        mem_peak = max(mem_after, mem_before)
        
        result = BenchmarkResult(
            name=name,
            execution_time=execution_time,
            memory_used=mem_used,
            memory_peak=mem_peak,
            success=success,
            error=error
        )
        
        self.results.append(result)
        return result
    
    def print_results(self):
        """Imprime resultados del benchmark."""
        print("\n" + "="*70)
        print(" RESULTADOS DEL BENCHMARK ")
        print("="*70)
        
        for result in self.results:
            status = "✅" if result.success else "❌"
            print(f"\n{status} {result.name}")
            print(f"   Tiempo: {result.execution_time:.3f}s")
            print(f"   Memoria usada: {result.memory_used}MB")
            print(f"   Memoria peak: {result.memory_peak}MB")
            
            if not result.success:
                print(f"   Error: {result.error}")
        
        # Resumen
        print("\n" + "-"*70)
        print(" RESUMEN ")
        print("-"*70)
        
        total_time = sum(r.execution_time for r in self.results)
        avg_time = total_time / len(self.results) if self.results else 0
        success_count = sum(1 for r in self.results if r.success)
        
        print(f"Total tests: {len(self.results)}")
        print(f"Exitosos: {success_count}/{len(self.results)}")
        print(f"Tiempo total: {total_time:.3f}s")
        print(f"Tiempo promedio: {avg_time:.3f}s")
        print(f"Memoria peak total: {max(r.memory_peak for r in self.results)}MB")


# ============================================================================
# BENCHMARKS ESPECÍFICOS
# ============================================================================

async def benchmark_regex_engine():
    """Benchmark para el motor regex (Nivel 1)."""
    from src.engine.nivel_1_regex import RegexEngine
    
    engine = RegexEngine()
    
    # Test 1000 queries
    test_queries = [
        "abrir chrome",
        "buscar python tutorial",
        "crear archivo test.txt",
        "calcular 2+2",
        "hora actual",
    ] * 200  # 1000 queries total
    
    for query in test_queries:
        engine.match(query, "abrir|buscar|crear|calcular|hora")


async def benchmark_fuzzy_engine():
    """Benchmark para el motor fuzzy (Nivel 2)."""
    from src.engine.nivel_2_fuzzy import FuzzyEngine
    
    engine = FuzzyEngine()
    
    # Test 500 queries
    test_queries = [
        ("abrir crom", "abrir chrome"),
        ("busca piton", "buscar python"),
        ("hola mundo", "hola mundo"),
        ("crear archibo", "crear archivo"),
        ("kalkular", "calcular"),
    ] * 100  # 500 queries total
    
    for query, target in test_queries:
        engine.match(query, target)


async def benchmark_semantic_engine():
    """Benchmark para el motor semántico (Nivel 3)."""
    from src.engine.nivel_3_semantic import SemanticEngine
    
    # Solo si el modelo está disponible
    model_path = Path("models/all-MiniLM-L6-v2.onnx")
    if not model_path.exists():
        print("⚠️  Modelo ONNX no disponible, saltando benchmark semántico")
        return
    
    engine = SemanticEngine(model_path=str(model_path))
    
    # Test 50 queries (más lento por ONNX)
    test_queries = [
        "¿cómo está el clima hoy?",
        "necesito información sobre Python",
        "¿cuál es la capital de Francia?",
        "cómo crear una aplicación web",
        "explicación de machine learning",
    ] * 10  # 50 queries total
    
    for query in test_queries:
        await engine.embed_query(query)


async def benchmark_hybrid_engine():
    """Benchmark para el motor híbrido completo."""
    from src.hybrid_engine import HybridEngine
    
    engine = HybridEngine()
    
    # Test 100 queries
    test_queries = [
        "abrir chrome",
        "buscar información sobre Python",
        "crear un script de backup",
        "calcular raíz cuadrada de 16",
        "¿qué hora es?",
    ] * 20  # 100 queries total
    
    for query in test_queries:
        await engine.process_query(query)


async def benchmark_swarm_manager():
    """Benchmark para Swarm Manager."""
    from src.agents.swarm_manager import SwarmManager
    from src.agents.google_searcher import GoogleSearcher
    
    swarm = SwarmManager(max_concurrent_agents=2)
    swarm.add_agent("google", GoogleSearcher())
    
    # Test 10 queries (con red, más lento)
    test_queries = [
        "Python programming",
        "machine learning tutorial",
        "web development 2024",
    ] * 3  # 9 queries + 1 extra
    
    for query in test_queries[:10]:
        await swarm.execute_swarm(query, max_results_per_agent=3)


async def benchmark_code_generation():
    """Benchmark para Code Generation."""
    from src.code_gen.template_engine import TemplateEngine
    
    engine = TemplateEngine()
    
    # Test 50 generaciones
    contexts = [
        {"app_type": "calculadora", "interface": "cli"},
        {"app_type": "scraper", "interface": "cli"},
        {"app_type": "api", "interface": "flask"},
        {"app_type": "bot", "interface": "telegram"},
        {"app_type": "scheduler", "interface": "cli"},
    ] * 10  # 50 generaciones total
    
    for context in contexts:
        engine.generate("cli_app.py.template", context)


async def benchmark_vector_store():
    """Benchmark para Vector Store (SQLite)."""
    from src.persistence.vector_store_sqlite import VectorStore
    
    store = VectorStore(db_path=":memory:")
    
    # Test 1000 inserciones
    test_vectors = [
        ([0.1, 0.2, 0.3, 0.4], {"text": f"documento {i}"}),
        ([0.5, 0.6, 0.7, 0.8], {"text": f"documento {i+1}"}),
    ] * 500  # 1000 inserciones total
    
    for vector, metadata in test_vectors:
        store.insert(vector, metadata)
    
    # Test 100 búsquedas
    for i in range(100):
        store.search([0.1, 0.2, 0.3, 0.4], top_k=5)


# ============================================================================
# EJECUCIÓN DEL BENCHMARK
# ============================================================================

async def run_all_benchmarks():
    """Ejecuta todos los benchmarks."""
    benchmark = PerformanceBenchmark()
    
    print("\n" + "🦁 "*20)
    print(" Claw-Litle - Benchmark de Rendimiento")
    print("🦁 "*20)
    
    # Benchmark 1: Regex Engine
    print("\n📏 Ejecutando benchmark Regex Engine...")
    benchmark.measure_function("Regex Engine (1000 queries)", benchmark_regex_engine)
    
    # Benchmark 2: Fuzzy Engine
    print("\n📏 Ejecutando benchmark Fuzzy Engine...")
    benchmark.measure_function("Fuzzy Engine (500 queries)", benchmark_fuzzy_engine)
    
    # Benchmark 3: Semantic Engine
    print("\n📏 Ejecutando benchmark Semantic Engine...")
    benchmark.measure_function("Semantic Engine (50 queries)", benchmark_semantic_engine)
    
    # Benchmark 4: Hybrid Engine
    print("\n📏 Ejecutando benchmark Hybrid Engine...")
    benchmark.measure_function("Hybrid Engine (100 queries)", benchmark_hybrid_engine)
    
    # Benchmark 5: Swarm Manager
    print("\n📏 Ejecutando benchmark Swarm Manager...")
    benchmark.measure_function("Swarm Manager (10 queries)", benchmark_swarm_manager)
    
    # Benchmark 6: Code Generation
    print("\n📏 Ejecutando benchmark Code Generation...")
    benchmark.measure_function("Code Generation (50 templates)", benchmark_code_generation)
    
    # Benchmark 7: Vector Store
    print("\n📏 Ejecutando benchmark Vector Store...")
    benchmark.measure_function("Vector Store (1000 insert + 100 search)", benchmark_vector_store)
    
    # Imprimir resultados
    benchmark.print_results()
    
    # Verificar límites
    print("\n" + "="*70)
    print(" VERIFICACIÓN DE LÍMITES ")
    print("="*70)
    
    memory_limit = 350  # MB (límite para Termux)
    time_limit = 30  # segundos por operación
    
    peak_memory = max(r.memory_peak for r in benchmark.results)
    slowest_op = max(benchmark.results, key=lambda r: r.execution_time)
    
    print(f"\n📱 Límite RAM: {memory_limit}MB")
    print(f"   Peak medido: {peak_memory}MB")
    print(f"   Estado: {'✅ DENTRO DEL LÍMITE' if peak_memory < memory_limit else '❌ EXCEDE LÍMITE'}")
    
    print(f"\n⏱️  Límite tiempo por operación: {time_limit}s")
    print(f"   Operación más lenta: {slowest_op.name}")
    print(f"   Tiempo: {slowest_op.execution_time:.3f}s")
    print(f"   Estado: {'✅ DENTRO DEL LÍMITE' if slowest_op.execution_time < time_limit else '❌ EXCEDE LÍMITE'}")
    
    return benchmark


def main():
    """Función principal."""
    try:
        benchmark = asyncio.run(run_all_benchmarks())
        
        # Guardar resultados en archivo
        results_file = Path("benchmark_results.txt")
        with open(results_file, "w") as f:
            f.write("Claw-Litle - Resultados del Benchmark\n")
            f.write("="*50 + "\n\n")
            for result in benchmark.results:
                f.write(f"{result.name}: {result.execution_time:.3f}s, {result.memory_used}MB\n")
        
        print(f"\n📄 Resultados guardados en {results_file}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Benchmark cancelado por el usuario")
    except Exception as e:
        print(f"\n❌ Error durante el benchmark: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()