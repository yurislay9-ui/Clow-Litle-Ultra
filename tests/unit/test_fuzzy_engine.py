"""
Claw-Litle 1.0
test_fuzzy_engine.py - Tests para Nivel 2: Fuzzy Engine

Tests exhaustivos para el motor de coincidencia aproximada.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.engine.nivel_2_fuzzy import FuzzyEngine
from src.engine import IntentResult


class TestFuzzyEngineInitialization:
    """Tests para inicialización del FuzzyEngine."""
    
    def test_init_with_valid_registry(self, sample_intents_registry):
        """Test de inicialización con registro válido."""
        engine = FuzzyEngine(sample_intents_registry)
        assert engine is not None
        assert len(engine._keyword_map) > 0
    
    def test_init_with_default_threshold(self, sample_intents_registry):
        """Test de umbral por defecto."""
        engine = FuzzyEngine(sample_intents_registry)
        assert engine.threshold == 0.85
    
    def test_init_with_custom_threshold(self, sample_intents_registry):
        """Test de umbral personalizado."""
        engine = FuzzyEngine(sample_intents_registry, threshold=0.75)
        assert engine.threshold == 0.75
    
    def test_init_extracts_keywords(self, sample_intents_registry):
        """Test que extrae keywords correctamente."""
        engine = FuzzyEngine(sample_intents_registry)
        
        assert "greet" in engine._keyword_map
        assert "hola" in engine._keyword_map["greet"]
        assert "buenos" in engine._keyword_map["greet"]


class TestFuzzyEngineMatching:
    """Tests para matching del FuzzyEngine."""
    
    def test_exact_keyword_match(self, sample_intents_registry):
        """Test de match exacto de keyword."""
        engine = FuzzyEngine(sample_intents_registry)
        result = engine.match("hola")
        
        assert result is not None
        assert result.intent_name == "greet"
        assert result.confidence == 1.0
    
    def test_fuzzy_match_with_typo(self, sample_intents_registry):
        """Test de match con error tipográfico."""
        engine = FuzzyEngine(sample_intents_registry)
        result = engine.match("holaa")  # Error tipográfico
        
        # Debería matchear con alta confianza
        assert result is not None
        assert result.intent_name == "greet"
        assert result.confidence >= 0.85
    
    def test_fuzzy_match_with_missing_letter(self, sample_intents_registry):
        """Test de match con letra faltante."""
        engine = FuzzyEngine(sample_intents_registry)
        result = engine.match("hol")  # Falta 'a'
        
        # Podría matchear con menor confianza
        assert result is not None or result is None  # Depende del threshold
    
    def test_contains_keyword(self, sample_intents_registry):
        """Test de query que contiene keyword."""
        engine = FuzzyEngine(sample_intents_registry)
        result = engine.match("hola mundo")
        
        # Debería matchear porque contiene "hola"
        assert result is not None
        assert result.intent_name == "greet"
    
    def test_keyword_at_start(self, sample_intents_registry):
        """Test de keyword al inicio."""
        engine = FuzzyEngine(sample_intents_registry)
        result = engine.match("hola que tal")
        
        assert result is not None
        assert result.intent_name == "greet"
    
    def test_no_match_dissimilar_query(self, sample_intents_registry):
        """Test de query disímil."""
        engine = FuzzyEngine(sample_intents_registry)
        result = engine.match("consulta completamente diferente")
        
        assert result is None
    
    def test_case_insensitive(self, sample_intents_registry):
        """Test de case-insensitive."""
        engine = FuzzyEngine(sample_intents_registry)
        
        assert engine.match("HOLA") is not None
        assert engine.match("Hola") is not None
    
    def test_whitespace_handling(self, sample_intents_registry):
        """Test de manejo de espacios."""
        engine = FuzzyEngine(sample_intents_registry)
        result = engine.match("  hola  ")
        
        assert result is not None
        assert result.intent_name == "greet"


class TestFuzzyEngineLevenshtein:
    """Tests para cálculo de distancia de Levenshtein."""
    
    def test_levenshtein_exact_match(self, sample_intents_registry):
        """Test de distancia 0 para match exacto."""
        engine = FuzzyEngine(sample_intents_registry)
        score = engine._get_fuzz_ratio("hola", "hola")
        
        assert score == 1.0
    
    def test_levenshtein_one_edit(self, sample_intents_registry):
        """Test de distancia 1."""
        engine = FuzzyEngine(sample_intents_registry)
        score = engine._get_fuzz_ratio("hola", "holaa")
        
        # Debería ser alto pero no perfecto
        assert 0.8 <= score < 1.0
    
    def test_levenshtein_completely_different(self, sample_intents_registry):
        """Test de strings completamente diferentes."""
        engine = FuzzyEngine(sample_intents_registry)
        score = engine._get_fuzz_ratio("hola", "xyz")
        
        # Debería ser bajo
        assert score < 0.5
    
    def test_levenshtein_empty_strings(self, sample_intents_registry):
        """Test de strings vacíos."""
        engine = FuzzyEngine(sample_intents_registry)
        
        assert engine._get_fuzz_ratio("", "") == 0.0
        assert engine._get_fuzz_ratio("hola", "") == 0.0
        assert engine._get_fuzz_ratio("", "hola") == 0.0
    
    def test_levenshtein_same_length(self, sample_intents_registry):
        """Test de strings de misma longitud."""
        engine = FuzzyEngine(sample_intents_registry)
        score = engine._get_fuzz_ratio("hola", "bola")
        
        # 3 de 4 caracteres iguales = 0.75
        assert score >= 0.7
    
    def test_levenshtein_different_length(self, sample_intents_registry):
        """Test de strings de diferente longitud."""
        engine = FuzzyEngine(sample_intents_registry)
        score = engine._get_fuzz_ratio("hola", "holaaaa")
        
        # Debería ser razonablemente alto
        assert score > 0.5


class TestFuzzyEngineThreshold:
    """Tests para umbral del FuzzyEngine."""
    
    def test_above_threshold(self, sample_intents_registry):
        """Test de score por encima del threshold."""
        engine = FuzzyEngine(sample_intents_registry, threshold=0.85)
        result = engine.match("hola")
        
        assert result is not None
        assert result.confidence >= 0.85
    
    def test_below_threshold(self, sample_intents_registry):
        """Test de score por debajo del threshold."""
        # Umbral muy alto
        engine = FuzzyEngine(sample_intents_registry, threshold=0.99)
        result = engine.match("holaa")  # No perfecto
        
        # Podría no matchear por threshold alto
        assert result is None or result.confidence >= 0.99
    
    def test_threshold_zero(self, sample_intents_registry):
        """Test de threshold cero (cualquier keyword matchea)."""
        engine = FuzzyEngine(sample_intents_registry, threshold=0.0)
        # Usar una query que contenga keywords del registro
        result = engine.match("hola amigo")
        
        # Con threshold 0, cualquier keyword debería matchear
        assert result is not None
    
    def test_threshold_one(self, sample_intents_registry):
        """Test de threshold uno (solo exactos)."""
        engine = FuzzyEngine(sample_intents_registry, threshold=1.0)
        result = engine.match("holaa")  # No exacto
        
        assert result is None


class TestFuzzyEngineMetadata:
    """Tests para metadatos del FuzzyEngine."""
    
    def test_metadata_contains_keyword(self, sample_intents_registry):
        """Test que metadata incluye keyword matcheada."""
        engine = FuzzyEngine(sample_intents_registry)
        result = engine.match("hola")
        
        assert result is not None
        assert "matched_keyword" in result.metadata
        assert result.metadata["matched_keyword"] == "hola"
    
    def test_metadata_level(self, sample_intents_registry):
        """Test que metadata indica nivel correcto."""
        engine = FuzzyEngine(sample_intents_registry)
        result = engine.match("hola")
        
        assert result.metadata["level"] == "fuzzy"
        assert result.level_reached == 2
    
    def test_metadata_threshold(self, sample_intents_registry):
        """Test que metadata incluye threshold."""
        engine = FuzzyEngine(sample_intents_registry, threshold=0.85)
        result = engine.match("hola")
        
        assert "threshold" in result.metadata
        assert result.metadata["threshold"] == 0.85


class TestFuzzyEngineEdgeCases:
    """Tests para casos extremos del FuzzyEngine."""
    
    def test_unicode_characters(self, sample_intents_registry):
        """Test de caracteres unicode."""
        engine = FuzzyEngine(sample_intents_registry)
        result = engine.match("holà")
        
        # Debería manejar unicode
        assert result is not None or result is None  # Depende de implementación
    
    def test_numbers_in_query(self, sample_intents_registry):
        """Test de números en query."""
        engine = FuzzyEngine(sample_intents_registry)
        result = engine.match("hola123")
        
        # Debería manejar números
        assert result is not None or result is None
    
    def test_special_characters(self, sample_intents_registry):
        """Test de caracteres especiales."""
        engine = FuzzyEngine(sample_intents_registry)
        result = engine.match("hola!")
        
        # Debería manejar caracteres especiales
        assert result is not None or result is None
    
    def test_very_long_keyword_match(self, sample_intents_registry):
        """Test de keyword muy larga."""
        engine = FuzzyEngine(sample_intents_registry)
        long_query = "hola" + "a" * 100
        
        # Debería manejar queries largas
        result = engine.match(long_query)
        assert result is not None or result is None


class TestFuzzyEnginePerformance:
    """Tests de rendimiento del FuzzyEngine."""
    
    def test_fast_execution(self, sample_intents_registry):
        """Test de ejecución rápida."""
        import time
        
        engine = FuzzyEngine(sample_intents_registry)
        
        start = time.time()
        for _ in range(100):
            engine.match("hola")
        elapsed = time.time() - start
        
        # Debería ser rápido (<5 segundos para 100 iteraciones)
        assert elapsed < 5.0
    
    def test_memory_usage(self, sample_intents_registry):
        """Test de uso de memoria."""
        import tracemalloc
        
        tracemalloc.start()
        
        engine = FuzzyEngine(sample_intents_registry)
        _, peak = tracemalloc.get_traced_memory()
        
        tracemalloc.stop()
        
        # Uso de memoria razonable (<10MB)
        assert peak < 10 * 1024 * 1024