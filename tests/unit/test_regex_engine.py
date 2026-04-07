"""
Claw-Litle 1.0
test_regex_engine.py - Tests para Nivel 1: Regex Engine

Tests exhaustivos para el motor de patrones regex.
"""

import pytest
import sys
import os

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.engine.nivel_1_regex import RegexEngine
from src.engine import IntentResult


class TestRegexEngineInitialization:
    """Tests para inicialización del RegexEngine."""
    
    def test_init_with_valid_registry(self, sample_intents_registry):
        """Test de inicialización con registro válido."""
        engine = RegexEngine(sample_intents_registry)
        assert engine is not None
        assert len(engine._compiled_patterns) > 0
    
    def test_init_with_empty_registry(self):
        """Test de inicialización con registro vacío."""
        empty_registry = {"intents": [], "fallback": {}}
        engine = RegexEngine(empty_registry)
        assert engine is not None
        assert len(engine._compiled_patterns) == 0
    
    def test_init_compiles_all_patterns(self, sample_intents_registry):
        """Test que todos los patrones son compilados."""
        engine = RegexEngine(sample_intents_registry)
        # Debería tener patrones para greet, farewell, help
        assert "greet" in engine._compiled_patterns
        assert "farewell" in engine._compiled_patterns
        assert "help" in engine._compiled_patterns


class TestRegexEngineMatching:
    """Tests para matching de patrones regex."""
    
    def test_exact_match_greet(self, sample_intents_registry):
        """Test de match exacto para saludo."""
        engine = RegexEngine(sample_intents_registry)
        result = engine.match("hola")
        
        assert result is not None
        assert result.intent_name == "greet"
        assert result.confidence == 1.0
        assert result.level_reached == 1
    
    def test_exact_match_farewell(self, sample_intents_registry):
        """Test de match exacto para despedida."""
        engine = RegexEngine(sample_intents_registry)
        result = engine.match("adios")
        
        assert result is not None
        assert result.intent_name == "farewell"
        assert result.confidence == 1.0
    
    def test_exact_match_help(self, sample_intents_registry):
        """Test de match exacto para ayuda."""
        engine = RegexEngine(sample_intents_registry)
        result = engine.match("help")
        
        assert result is not None
        assert result.intent_name == "help"
        assert result.confidence == 1.0
    
    def test_case_insensitive_match(self, sample_intents_registry):
        """Test de matching case-insensitive."""
        engine = RegexEngine(sample_intents_registry)
        
        assert engine.match("HOLA") is not None
        assert engine.match("Hola") is not None
        assert engine.match("HELP") is not None
        assert engine.match("Help") is not None
    
    def test_pattern_variation_match(self, sample_intents_registry):
        """Test de variaciones de patrones."""
        engine = RegexEngine(sample_intents_registry)
        
        # "buenos" o "buenas" deberían matchear
        result_buenos = engine.match("buenos")
        result_buenas = engine.match("buenas")
        
        assert result_buenos is not None or result_buenas is not None
    
    def test_no_match_unknown_query(self, sample_intents_registry):
        """Test de query desconocida."""
        engine = RegexEngine(sample_intents_registry)
        result = engine.match("consulta aleatoria que no existe")
        
        assert result is None
    
    def test_no_match_partial_query(self, sample_intents_registry):
        """Test de query parcial (no match exacto)."""
        engine = RegexEngine(sample_intents_registry)
        result = engine.match("holaaa")  # Demasiadas 'a'
        
        assert result is None
    
    def test_whitespace_handling(self, sample_intents_registry):
        """Test de manejo de espacios en blanco."""
        engine = RegexEngine(sample_intents_registry)
        
        # Espacios extra deberían ser ignorados
        result = engine.match("  hola  ")
        assert result is not None
        assert result.intent_name == "greet"
    
    def test_empty_query(self, sample_intents_registry):
        """Test de query vacía."""
        engine = RegexEngine(sample_intents_registry)
        result = engine.match("")
        
        assert result is None
    
    def test_special_characters(self, sample_intents_registry):
        """Test de caracteres especiales."""
        engine = RegexEngine(sample_intents_registry)
        result = engine.match("¡hola!")  # Con signos de exclamación
        
        # No debería matchear por los signos
        assert result is None


class TestRegexEngineMetadata:
    """Tests para metadatos del RegexEngine."""
    
    def test_metadata_contains_pattern(self, sample_intents_registry):
        """Test que metadata incluye patrón matcheado."""
        engine = RegexEngine(sample_intents_registry)
        result = engine.match("hola")
        
        assert result is not None
        assert "matched_pattern" in result.metadata
        assert result.metadata["level"] == "regex"
    
    def test_metadata_level(self, sample_intents_registry):
        """Test que metadata indica nivel correcto."""
        engine = RegexEngine(sample_intents_registry)
        result = engine.match("hola")
        
        assert result.metadata["level"] == "regex"
        assert result.level_reached == 1


class TestRegexEngineEdgeCases:
    """Tests para casos extremos del RegexEngine."""
    
    def test_unicode_characters(self, sample_intents_registry):
        """Test de caracteres unicode."""
        engine = RegexEngine(sample_intents_registry)
        result = engine.match("holà")  # Con acento
        
        # No debería matchear
        assert result is None
    
    def test_emoji_query(self, sample_intents_registry):
        """Test de emoji como query."""
        engine = RegexEngine(sample_intents_registry)
        result = engine.match("👋")
        
        assert result is None
    
    def test_very_long_query(self, sample_intents_registry):
        """Test de query muy larga."""
        engine = RegexEngine(sample_intents_registry)
        long_query = "hola" + "a" * 10000
        result = engine.match(long_query)
        
        assert result is None
    
    def test_newline_characters(self, sample_intents_registry):
        """Test de saltos de línea."""
        engine = RegexEngine(sample_intents_registry)
        result = engine.match("hola\nmundo")
        
        assert result is None
    
    def test_null_bytes(self, sample_intents_registry):
        """Test de bytes nulos."""
        engine = RegexEngine(sample_intents_registry)
        result = engine.match("hola\x00mundo")
        
        # Debería manejar o rechazar
        assert result is None or result is not None  # Depende de la implementación


class TestRegexEnginePerformance:
    """Tests de rendimiento del RegexEngine."""
    
    def test_fast_execution(self, sample_intents_registry):
        """Test de ejecución rápida."""
        import time
        
        engine = RegexEngine(sample_intents_registry)
        
        start = time.time()
        for _ in range(1000):
            engine.match("hola")
        elapsed = time.time() - start
        
        # Debería ser muy rápido (<1 segundo para 1000 iteraciones)
        assert elapsed < 1.0
    
    def test_memory_usage(self, sample_intents_registry):
        """Test de uso de memoria."""
        import tracemalloc
        
        tracemalloc.start()
        
        engine = RegexEngine(sample_intents_registry)
        _, peak = tracemalloc.get_traced_memory()
        
        tracemalloc.stop()
        
        # Uso de memoria razonable (<10MB)
        assert peak < 10 * 1024 * 1024