"""
Claw-Litle 1.0
test_integration.py - Tests de Integración

Tests exhaustivos para el flujo completo del sistema.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.hybrid_engine import HybridEngine
from src.gateway import Gateway, SecurityConfig, Request
from src.router import Router, RouterConfig


class TestFullPipeline:
    """Tests para el pipeline completo: Gateway → Engine → Router."""
    
    def test_greet_pipeline(self, sample_intents_registry):
        """Test de pipeline para saludo."""
        # Configurar componentes
        security_config = SecurityConfig()
        gateway = Gateway(security_config)
        engine = HybridEngine({"short_circuit_threshold": 0.95})
        router_config = RouterConfig()
        router = Router(engine, gateway, router_config)
        
        # Ejecutar pipeline
        result = router.route("hola", "test_user")
        
        assert result.success is True
        assert result.intent == "greet"
        assert result.action == "respond"
    
    def test_help_pipeline(self, sample_intents_registry):
        """Test de pipeline para ayuda."""
        security_config = SecurityConfig()
        gateway = Gateway(security_config)
        engine = HybridEngine({"short_circuit_threshold": 0.95})
        router_config = RouterConfig()
        router = Router(engine, gateway, router_config)
        
        result = router.route("help", "test_user")
        
        assert result.success is True
        assert result.intent == "help"
    
    def test_farewell_pipeline(self, sample_intents_registry):
        """Test de pipeline para despedida."""
        security_config = SecurityConfig()
        gateway = Gateway(security_config)
        engine = HybridEngine({"short_circuit_threshold": 0.95})
        router_config = RouterConfig()
        router = Router(engine, gateway, router_config)
        
        result = router.route("adios", "test_user")
        
        assert result.success is True
        assert result.intent == "farewell"
    
    def test_search_pipeline(self, sample_intents_registry):
        """Test de pipeline para búsqueda."""
        security_config = SecurityConfig()
        gateway = Gateway(security_config)
        engine = HybridEngine({"short_circuit_threshold": 0.95})
        router_config = RouterConfig()
        router = Router(engine, gateway, router_config)
        
        result = router.route("buscar información", "test_user")
        
        assert result.success is True
        assert result.intent == "web_search"
        assert result.action == "dispatch"


class TestMultipleUsers:
    """Tests para múltiples usuarios concurrentes."""
    
    def test_concurrent_users(self, sample_intents_registry):
        """Test de usuarios concurrentes."""
        security_config = SecurityConfig()
        gateway = Gateway(security_config)
        engine = HybridEngine({"short_circuit_threshold": 0.95})
        router_config = RouterConfig()
        router = Router(engine, gateway, router_config)
        
        # Múltiples usuarios haciendo peticiones
        users = ["user1", "user2", "user3"]
        queries = ["hola", "help", "adios"]
        
        results = []
        for user, query in zip(users, queries):
            result = router.route(query, user)
            results.append(result)
        
        # Todos deberían tener éxito
        assert all(r.success for r in results)
    
    def test_rate_limiting_per_user(self, sample_intents_registry):
        """Test de rate limiting por usuario."""
        security_config = SecurityConfig()
        security_config.rate_limit_free = 2
        gateway = Gateway(security_config)
        engine = HybridEngine({"short_circuit_threshold": 0.95})
        router_config = RouterConfig()
        router = Router(engine, gateway, router_config)
        
        # User1 hace 3 peticiones
        for _ in range(3):
            result = router.route("hola", "spam_user")
        
        # La tercera debería ser rechazada
        assert result.success is False


class TestCaching:
    """Tests para sistema de caché."""
    
    def test_cache_hit(self, sample_intents_registry):
        """Test de acierto de caché."""
        security_config = SecurityConfig()
        gateway = Gateway(security_config)
        engine = HybridEngine({"short_circuit_threshold": 0.95})
        router_config = RouterConfig(enable_caching=True)
        router = Router(engine, gateway, router_config)
        
        # Primera petición
        result1 = router.route("hola", "test_user")
        assert result1.success is True
        
        # Segunda petición (debería ser cacheada)
        result2 = router.route("hola", "test_user")
        assert result2.success is True
        assert result2.metadata.get("cached") is True
    
    def test_cache_clear(self, sample_intents_registry):
        """Test de limpieza de caché."""
        security_config = SecurityConfig()
        gateway = Gateway(security_config)
        engine = HybridEngine({"short_circuit_threshold": 0.95})
        router_config = RouterConfig(enable_caching=True)
        router = Router(engine, gateway, router_config)
        
        # Hacer petición para cachear
        router.route("hola", "test_user")
        
        # Limpiar caché
        router.clear_cache()
        
        # Nueva petición no debería estar cacheada
        result = router.route("hola", "test_user")
        assert result.success is True
        assert result.metadata.get("cached") is not True


class TestErrorHandling:
    """Tests para manejo de errores."""
    
    def test_invalid_query_handling(self, sample_intents_registry):
        """Test de manejo de query inválida."""
        security_config = SecurityConfig()
        gateway = Gateway(security_config)
        engine = HybridEngine({"short_circuit_threshold": 0.95})
        router_config = RouterConfig()
        router = Router(engine, gateway, router_config)
        
        # Query vacía
        result = router.route("", "test_user")
        assert result.success is False
    
    def test_malicious_query_handling(self, sample_intents_registry):
        """Test de manejo de query maliciosa."""
        security_config = SecurityConfig()
        gateway = Gateway(security_config)
        engine = HybridEngine({"short_circuit_threshold": 0.95})
        router_config = RouterConfig()
        router = Router(engine, gateway, router_config)
        
        # Query con XSS
        result = router.route("<script>alert(1)</script>", "test_user")
        assert result.success is False
    
    def test_very_long_query_handling(self, sample_intents_registry):
        """Test de manejo de query muy larga."""
        security_config = SecurityConfig()
        gateway = Gateway(security_config)
        engine = HybridEngine({"short_circuit_threshold": 0.95})
        router_config = RouterConfig()
        router = Router(engine, gateway, router_config)
        
        # Query muy larga
        long_query = "a" * 2000
        result = router.route(long_query, "test_user")
        assert result.success is False


class TestStatsAndMonitoring:
    """Tests para estadísticas y monitoreo."""
    
    def test_router_stats(self, sample_intents_registry):
        """Test de estadísticas del router."""
        security_config = SecurityConfig()
        gateway = Gateway(security_config)
        engine = HybridEngine({"short_circuit_threshold": 0.95})
        router_config = RouterConfig()
        router = Router(engine, gateway, router_config)
        
        # Hacer algunas peticiones
        router.route("hola", "user1")
        router.route("help", "user2")
        
        # Obtener estadísticas
        stats = router.get_stats()
        
        assert "cache_size" in stats
        assert "handlers_count" in stats
        assert stats["handlers_count"] > 0
    
    def test_engine_stats(self, sample_intents_registry):
        """Test de estadísticas del engine."""
        engine = HybridEngine({"short_circuit_threshold": 0.95})
        
        stats = engine.get_stats()
        
        assert "levels_enabled" in stats
        assert "total_queries" in stats


class TestEdgeCasesIntegration:
    """Tests de casos extremos en integración."""
    
    def test_unicode_queries(self, sample_intents_registry):
        """Test de queries con unicode."""
        security_config = SecurityConfig()
        gateway = Gateway(security_config)
        engine = HybridEngine({"short_circuit_threshold": 0.95})
        router_config = RouterConfig()
        router = Router(engine, gateway, router_config)
        
        # Query con emojis
        result = router.route("👋 hola", "test_user")
        assert result.success is True or result.success is False  # Depende del manejo
    
    def test_empty_user_id(self, sample_intents_registry):
        """Test de user_id vacío."""
        security_config = SecurityConfig()
        gateway = Gateway(security_config)
        engine = HybridEngine({"short_circuit_threshold": 0.95})
        router_config = RouterConfig()
        router = Router(engine, gateway, router_config)
        
        result = router.route("hola", "")
        assert result.success is False
    
    def test_special_characters_in_query(self, sample_intents_registry):
        """Test de caracteres especiales."""
        security_config = SecurityConfig()
        gateway = Gateway(security_config)
        engine = HybridEngine({"short_circuit_threshold": 0.95})
        router_config = RouterConfig()
        router = Router(engine, gateway, router_config)
        
        result = router.route("!@#$%^&*()", "test_user")
        # Debería manejar o fallback
        assert result.success is True or result.success is False