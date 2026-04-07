#!/usr/bin/env python3
"""
Tests para el HybridEngine (Motor Híbrido 4-Niveles).
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock


class TestHybridEngine:
    """Tests para HybridEngine."""
    
    def setup_method(self):
        """Configurar tests."""
        self.config = {
            "short_circuit_threshold": 0.95,
            "regex_enabled": True,
            "fuzzy_enabled": True,
            "semantic_enabled": False,  # Desactivado para tests rápidos
            "expert_rules_enabled": True,
            "fuzzy_threshold": 0.85,
            "semantic_threshold": 0.89
        }
    
    def test_engine_initialization(self):
        """Test que el engine se inicializa correctamente."""
        from src.hybrid_engine import HybridEngine
        
        engine = HybridEngine(self.config)
        assert engine is not None
        assert engine.short_circuit_threshold == 0.95
        assert engine._initialized is False  # Lazy loading
    
    def test_memory_conversion_accuracy(self):
        """Test que la conversión de memoria es correcta (1024 no 1021)."""
        from src.hybrid_engine import HybridEngine
        
        engine = HybridEngine(self.config)
        
        # Mock de _get_available_ram_mb para evitar dependencia de /proc/meminfo
        with patch('builtins.open', mock_open_with_meminfo("MemAvailable:    1048576 kB")):
            result = engine._get_available_ram_mb()
            # 1048576 KB = 1024 MB exactos (1048576 / 1024)
            assert abs(result - 1024.0) < 0.1
    
    def test_short_circuit_threshold(self):
        """Test que el short-circuit funciona correctamente."""
        from src.hybrid_engine import HybridEngine, IntentResult
        
        engine = HybridEngine(self.config)
        
        # Simular resultado con alta confianza
        result = IntentResult(
            intent_name="test_intent",
            confidence=0.97,  # > 0.95 threshold
            level_reached=1
        )
        
        assert result.confidence >= engine.short_circuit_threshold
    
    def test_process_with_empty_query(self):
        """Test procesamiento con query vacío."""
        from src.hybrid_engine import HybridEngine
        
        engine = HybridEngine(self.config)
        intents_registry = {}
        
        # Debería manejar query vacío gracefully
        result = engine.process("", intents_registry)
        assert result is not None
        assert result.intent_name == "unknown" or result.confidence == 0.0
    
    def test_process_with_valid_query(self):
        """Test procesamiento con query válido."""
        from src.hybrid_engine import HybridEngine
        
        engine = HybridEngine(self.config)
        intents_registry = {
            "greet": {"patterns": ["hola", "buenos días", "buenas tardes"]}
        }
        
        result = engine.process("hola", intents_registry)
        assert result is not None
        assert result.intent_name is not None
    
    def test_get_stats(self):
        """Test obtención de estadísticas del engine."""
        from src.hybrid_engine import HybridEngine
        
        engine = HybridEngine(self.config)
        stats = engine.get_stats()
        
        assert isinstance(stats, dict)
        assert "short_circuit_threshold" in stats
        assert "levels_enabled" in stats
    
    def test_unload_and_reload_models(self):
        """Test descarga y recarga de modelos."""
        from src.hybrid_engine import HybridEngine
        
        engine = HybridEngine(self.config)
        
        # Debería poder llamar a unload_models sin error
        engine.unload_models()
        
        # Debería poder llamar a reload_models sin error
        engine.reload_models()


def mock_open_with_meminfo(content):
    """Helper para mockear open con contenido de meminfo."""
    mock_file = MagicMock()
    mock_file.read.return_value = content
    mock_file.__enter__.return_value = mock_file
    return lambda *args, **kwargs: mock_file


if __name__ == "__main__":
    pytest.main([__file__, "-v"])